# Copyright (c) 2020-2021 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
# pylint: disable=C0103
import enum
import datetime
from typing import Any, Dict, List, Union, Optional, NamedTuple

from transmission_rpc.utils import _camel_to_snake, format_timedelta
from transmission_rpc.constants import Priority, LimitMode
from transmission_rpc.lib_types import _Base


class File(NamedTuple):
    name: str  # file name
    size: int  # file size in bytes
    bytes_complete: int  # bytes completed
    priority: Priority
    wanted: bool  # if selected for download


class TorrentStatus(enum.IntEnum):
    """Torrent status enumeration

    returned by :py:attr:`Torrent.status`
    """

    stopped = 0
    check_pending = 1
    checking = 2
    download_pending = 3
    downloading = 4
    seed_pending = 5
    seeding = 6


class Torrent(_Base):
    """
    Torrent is a class holding the data received from
    Transmission regarding a bittorrent transfer.

    All fetched torrent fields are accessible through this class using attributes.
    This class has a few convenience properties using the torrent data.
    """

    def __init__(self, fields: Dict[str, Any]):
        if "id" not in fields and "hashString" not in fields:
            raise ValueError("Torrent requires an 'id' field or 'hashString' field")
        super().__init__(fields)

    @property
    def id(self) -> int:
        """The id for this torrent"""
        return self._get("id")

    def _get_name_string(self) -> Optional[str]:
        """Get the name"""
        # try to find an identifier
        if "name" in self._fields:
            return self.name
        if "hash_string" in self._fields:
            return self.hash_string
        if "id" in self._fields:
            return str(self.id)
        return "..."

    def __repr__(self) -> str:
        name = self._get_name_string()
        return f'<Torrent "{name}">'

    def __str__(self) -> str:
        name = self._get_name_string()
        return f'<Torrent "{name}">'

    @property
    def hash_string(self) -> str:
        """torrent info hash"""
        return self._get("hash_string")

    def get(self, name: str, default: Any = None) -> Optional[Any]:
        """get a raw field value"""
        return self._fields.get(_camel_to_snake(name), default)

    @property
    def name(self) -> str:
        """Returns the name of this torrent.

        Raise AttributeError if server don't return this field
        """
        return self._get("name")

    @property
    def status(self) -> TorrentStatus:
        """
        Returns the torrent status. Is either one of [0,6] 'check pending', 'checking',
        'downloading', 'download pending', 'seeding', 'seed pending' or 'stopped'.
        The first two is related to verification.

        see :py:class:`TorrentStatus` for details

        Examples:

        .. code-block:: python

            from transmission_rpc import TorrentStatus

            torrent = Torrent()
            assert torrent.status == TorrentStatus.downloading
        """
        return TorrentStatus(self._get("status"))

    @property
    def progress(self) -> float:
        """
        download progress in range [0, 100].

        """
        try:
            # https://gist.github.com/jackiekazil/6201722#gistcomment-2788556
            # percentDone is added at rpc 5
            return round(100 * self.percent_done, 2)
        except KeyError:
            try:
                size = self.size_when_done
                left = self.left_until_done
                return round(100 * (size - left) / size, 2)
            except ZeroDivisionError:
                return 0

    @property
    def ratio(self) -> float:
        """
        upload/download ratio.
        """
        return float(self._get("upload_ratio"))

    @property
    def eta(self) -> Optional[datetime.timedelta]:
        """
        the "eta" as datetime.timedelta.
        """
        eta = self._get("eta")
        if eta >= 0:
            return datetime.timedelta(seconds=eta)
        return None

    @property
    def date_active(self) -> datetime.datetime:
        """the attribute ``activityDate`` as ``datetime.datetime`` in **UTC timezone**.

        .. note::

            raw ``activityDate`` value could be ``0`` for never activated torrent,
            therefore it can't always be converted to local timezone.
        """
        return datetime.datetime.fromtimestamp(
            self._fields["activity_date"], datetime.timezone.utc
        )

    @property
    def date_added(self) -> datetime.datetime:
        """raw field ``addedDate`` as ``datetime.datetime`` in **local timezone**."""
        return datetime.datetime.fromtimestamp(self._fields["added_date"]).astimezone()

    @property
    def date_started(self) -> datetime.datetime:
        """raw field ``startDate`` as ``datetime.datetime`` in **local timezone**.

        :rtype: datetime.datetime
        """
        return datetime.datetime.fromtimestamp(
            self._fields["start_date"], datetime.timezone.utc
        )

    @property
    def date_done(self) -> Optional[datetime.datetime]:
        """
        the attribute "doneDate" as datetime.datetime.

        there is a bug in early version of transmission,
        this value is set to ``0`` for a pre-downloaded torrent, see
        `transmission#1971 <https://github.com/transmission/transmission/issues/1971>`
        for more details.

        returns ``done_added`` if "doneDate" is ``0`` and torrent is completed."""
        done_date = self._get("done_date")
        # Transmission might forget to set doneDate which is initialized to zero,
        # so if doneDate is zero return None
        if done_date == 0:
            if self.is_finished and self.downloaded_ever == 0:
                # pre-downloaded torrent
                return self.date_added
            return None
        return datetime.datetime.fromtimestamp(done_date).astimezone()

    def format_eta(self) -> str:
        """
        Returns the attribute *eta* formatted as a string.

        * If eta is -1 the result is 'not available'
        * If eta is -2 the result is 'unknown'
        * Otherwise eta is formatted as <days> <hours>:<minutes>:<seconds>.
        """
        eta = self._get("eta")
        if eta == -1:
            return "not available"
        if eta == -2:
            return "unknown"
        return format_timedelta(datetime.timedelta(seconds=eta))

    @property
    def download_dir(self) -> Optional[str]:
        """The download directory"""
        return self._get("download_dir")

    def files(self) -> List[File]:
        """
        Get list of files for this torrent.

        .. note ::

            The order of the files is guaranteed.
            The index of file object is the id of the file
            when calling :py:meth:`transmission_rpc.client.Client.set_files`.

        .. code-block:: python

            from transmission_rpc import Client

            torrent = Client().get_torrent(0)

            for file_id, file in enumerate(torrent.files()):
                print(file_id, file)

        """
        result: List[File] = []
        if "files" in self._fields:
            files = self._get("files")
            indices = range(len(files))
            priorities = self.priorities
            wanted = self.wanted
            for item in zip(indices, files, priorities, wanted):
                selected = bool(item[3])
                priority = item[2]
                result.append(
                    File(
                        wanted=selected,
                        priority=priority,
                        size=item[1]["length"],
                        name=item[1]["name"],
                        bytes_complete=item[1]["bytesCompleted"],
                    )
                )
        return result

    @property
    def rate_download(self) -> int:
        """
        Returns download rate in B/s
        """
        return self._get("rate_download")

    @property
    def rate_upload(self) -> int:
        """
        Returns upload rate in B/s
        """
        return self._get("rate_upload")

    @property
    def download_limit(self) -> Optional[int]:
        """The download limit.

        Can be a number or None.
        """
        if self._fields["download_limited"]:
            return self._fields["download_limit"]
        return None

    @property
    def peer_limit(self) -> int:
        """the peer limit."""
        return self._get("peer_limit")

    @property
    def bandwidth_priority(self) -> Priority:
        """
        Bandwidth priority as string.
        """

        return Priority(self._get("bandwidth_priority"))

    @property
    def seed_idle_limit(self) -> int:
        """
        seed idle limit in minutes.
        """
        return self._get("seed_idle_limit")

    @property
    def is_finished(self) -> bool:
        """Returns true if the torrent is finished"""
        return self._get("is_finished")

    @property
    def is_stalled(self) -> bool:
        """Returns true if the torrent is stalled"""
        return self._get("is_stalled")

    @property
    def size_when_done(self) -> int:
        """Size in bytes when the torrent is done"""
        return self._get("size_when_done")

    @property
    def total_size(self) -> int:
        """Total size in bytes"""
        return self._get("total_size")

    @property
    def left_until_done(self) -> int:
        """Bytes left until done"""
        return self._get("left_until_done")

    @property
    def desired_available(self) -> int:
        """Bytes that are left to download and available"""
        return self._get("desired_available")

    @property
    def available(self) -> float:
        """Availability in percent"""
        bytes_all = self.total_size
        bytes_done = sum(map(lambda x: x["bytesCompleted"], self._fields["file_stats"]))
        bytes_avail = self.desired_available + bytes_done
        return (bytes_avail / bytes_all) * 100 if bytes_all else 0

    @property
    def seed_idle_mode(self) -> LimitMode:
        """
        Seed idle mode as string. Can be one of 'global', 'single' or 'unlimited'.

         * global, use session seed idle limit.
         * single, use torrent seed idle limit. See seed_idle_limit.
         * unlimited, no seed idle limit.
        """
        return LimitMode(self._get("seed_idle_mode"))

    @property
    def seed_ratio_limit(self) -> float:
        """
        Torrent seed ratio limit as float. Also see seed_ratio_mode.
        This is a mutator.

        :rtype: float
        """

        return self._get("seed_ratio_limit")

    @property
    def seed_ratio_mode(self) -> LimitMode:
        """
         * global, use session seed ratio limit.
         * single, use torrent seed ratio limit. See seed_ratio_limit.
         * unlimited, no seed ratio limit.

        see :py:class:`LimitMode` for more details.

        This is a mutator.
        """
        return LimitMode(self._get("seed_ratio_mode"))

    @property
    def upload_limit(self) -> int:
        """
        upload limit.
        Can be a number or None.
        """
        return self._get("upload_limited")

    @property
    def queue_position(self) -> int:
        """queue position for this torrent."""
        return self._get("queue_position")

    @property
    def comment(self) -> str:
        """Torrent comment."""
        return self._get("comment")

    @property
    def corrupt_ever(self) -> int:
        """Number of bytes of corrupt data downloaded."""
        return self._get("corrupt_ever")

    @property
    def creator(self) -> str:
        """Torrent creator."""
        return self._get("creator")

    @property
    def date_created(self) -> int:
        """Torrent creation date."""
        return self._get("date_created")

    @property
    def download_limited(self) -> bool:
        """Download limit is enabled"""
        return self._get("download_limited")

    @property
    def downloaded_ever(self) -> int:
        """Number of bytes of good data downloaded."""
        return self._get("downloaded_ever")

    @property
    def edit_date(self) -> int:
        """editDate

        added rpc version 16"""
        return self._get("edit_date")

    @property
    def error(self) -> int:
        """Kind of error.

        * 0 means OK,
        * 1 means tracker warning
        * 2 means tracker error
        * 3 means local error."""
        return self._get("error")

    @property
    def error_string(self) -> str:
        """Error message."""
        return self._get("error_string")

    @property
    def eta_idle(self) -> Optional[datetime.timedelta]:
        """
        timedelta left until the idle time limit is reached.

        :available: transmission version 2.80
        :available: RPC version 15
        """
        eta = self._get("eta_idle")
        if eta < 0:
            return None
        return datetime.timedelta(seconds=eta)

    @property
    def file_stats(self) -> list:
        """use :py:meth:`Torrent.files`"""
        return self._get("file_stats")

    @property
    def have_unchecked(self) -> int:
        """Number of bytes of partial pieces."""
        return self._get("have_unchecked")

    @property
    def have_valid(self) -> int:
        """Number of bytes of checksum verified data."""
        return self._get("have_valid")

    @property
    def honors_session_limits(self) -> bool:
        """True if session upload limits are honored"""
        return self._get("honors_session_limits")

    @property
    def is_private(self) -> bool:
        """True if the torrent is private."""
        return self._get("is_private")

    @property
    def labels(self) -> list:
        """array of string labels

        added rpc version 16"""
        return self._get("labels")

    @property
    def magnet_link(self) -> str:
        """The magnet link for this torrent."""
        return self._get("magnet_link")

    @property
    def manual_announce_time(self) -> int:
        """The time until you manually ask for more peers."""
        return self._get("manual_announce_time")

    @property
    def max_connected_peers(self) -> int:
        """Maximum of connected peers."""
        return self._get("max_connected_peers")

    @property
    def metadata_percent_complete(self) -> int:
        """Download progress of metadata. 0.0 to 1.0."""
        return self._get("metadata_percent_complete")

    @property
    def peers(self) -> list:
        """Array of peer objects."""
        return self._get("peers")

    @property
    def peers_connected(self) -> int:
        """Number of peers we are connected to."""
        return self._get("peers_connected")

    @property
    def peers_from(self) -> dict:
        """Object containing download peers counts for different peer types."""
        return self._get("peers_from")

    @property
    def peers_getting_from_us(self) -> int:
        """Number of peers we are sending data to."""
        return self._get("peers_getting_from_us")

    @property
    def peers_sending_to_us(self) -> int:
        """Number of peers sending to us"""
        return self._get("peers_sending_to_us")

    @property
    def percent_done(self) -> Union[float, int]:
        """Download progress of selected files. range [0, 1]"""
        return self._get("percent_done")

    @property
    def piece_count(self) -> int:
        """Number of pieces."""
        return self._get("piece_count")

    @property
    def piece_size(self) -> int:
        """Number of bytes in a piece."""
        return self._get("piece_size")

    @property
    def pieces(self) -> str:
        """String with base64 encoded bitfield indicating finished pieces."""
        return self._get("pieces")

    @property
    def priorities(self) -> List[Priority]:
        """Array of file priorities."""
        return [Priority(x) for x in self._get("priorities")]

    @property
    def recheck_progress(self) -> int:
        """Progress of recheck. 0.0 to 1.0."""
        return self._get("recheck_progress")

    @property
    def seconds_downloading(self) -> int:
        """

        added rpc version 15"""
        return self._get("seconds_downloading")

    @property
    def seconds_seeding(self) -> int:
        """

        added rpc version 15"""
        return self._get("seconds_seeding")

    @property
    def torrent_file(self) -> str:
        """Path to .torrent file."""
        return self._get("torrent_file")

    @property
    def tracker_stats(self) -> list:
        """Array of object containing tracker statistics."""
        return self._get("tracker_stats")

    @property
    def trackers(self) -> list:
        """Array of tracker objects."""
        return self._get("trackers")

    @property
    def upload_limited(self) -> bool:
        """Upload limit enabled."""
        return self._get("upload_limited")

    @property
    def upload_ratio(self) -> int:
        """Seed ratio."""
        return self._get("upload_ratio")

    @property
    def uploaded_ever(self) -> int:
        """Number of bytes uploaded, ever."""
        return self._get("uploaded_ever")

    @property
    def wanted(self) -> List[int]:
        """Array of booleans indicated wanted files."""
        return self._get("wanted")

    @property
    def webseeds(self) -> list:
        """Array of webseeds objects"""
        return self._get("webseeds")

    @property
    def webseeds_sending_to_us(self) -> int:
        """Number of webseeds seeding to us."""
        return self._get("webseeds_sending_to_us")
