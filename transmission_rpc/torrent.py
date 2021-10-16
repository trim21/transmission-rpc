# Copyright (c) 2020-2021 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
# pylint: disable=C0103
import enum
import datetime
from typing import Any, Dict, List, TypeVar, Optional

from transmission_rpc.utils import _camel_to_snake, format_timedelta
from transmission_rpc.constants import Priority, LimitMode
from transmission_rpc.lib_types import File, _Base

T = TypeVar("T")


class TorrentStatus(enum.IntEnum):
    stopped = 0
    check_pending = 1
    checking = 2
    download_pending = 3
    downloading = 4
    seed_pending = 5
    seeding = 6


class Torrent(_Base):
    """
    Torrent is a class holding the data received from Transmission regarding a bittorrent transfer.

    All fetched torrent fields are accessible through this class using attributes.
    This class has a few convenience properties using the torrent data.
    """

    def __init__(self, fields: Dict[str, Any]):
        if "id" not in fields:
            raise ValueError("Torrent requires an id")
        super().__init__(fields)

    @property
    def id(self) -> int:
        """Returns the id for this torrent"""
        return self.__getattr__("id")

    def _get_name_string(self) -> Optional[str]:
        """Get the name"""
        name = None
        # try to find name
        if "name" in self._fields:
            name = self.__getattr__("name")
        return name

    def __repr__(self) -> str:
        tid = self.__getattr__("id")
        name = self._get_name_string()
        if name is not None:
            return f'<Torrent {tid} "{name}">'
        return f"<Torrent {tid}>"

    def __str__(self) -> str:
        name = self._get_name_string()
        if name is not None:
            return f'Torrent "{name}"'
        return "Torrent"

    def get(self, name: str, default: T = None) -> Optional[T]:
        v = self._fields.get(_camel_to_snake(name))
        if v is not None:
            return v.value
        return default

    def files(self) -> List[File]:
        """
        Get list of files for this torrent.

        .. note ::


            The order of the files is guaranteed. The index of file object is the id of the file
            when calling :py:meth:`transmission_rpc.client.Client.set_files`.

        .. code-block:: python

            from transmission_rpc import Client

            torrent = Client().get_torrent(0)

            for file_id, file in enumerate(torrent.files()):
                print(file_id, file)

        """
        result: List[File] = []
        if "files" in self._fields:
            files = self.__getattr__("files")
            indices = range(len(files))
            priorities = self.__getattr__("priorities")
            wanted = self.__getattr__("wanted")
            for item in zip(indices, files, priorities, wanted):
                selected = bool(item[3])
                priority = Priority[item[2]]
                result.append(
                    File(
                        selected=selected,
                        priority=priority,
                        size=item[1]["length"],
                        name=item[1]["name"],
                        completed=item[1]["bytesCompleted"],
                    )
                )
        return result

    @property
    def name(self) -> str:
        """Returns the name of this torrent.

        Raise AttributeError if server don't return this field
        """
        return self.__getattr__("name")

    @property
    def status(self) -> TorrentStatus:
        """
        Returns the torrent status. Is either one of 'check pending', 'checking',
        'downloading', 'download pending', 'seeding', 'seed pending' or 'stopped'.
        The first two is related to verification.

        Examples:

        .. code-block:: python
            torrent = Torrent()
            assert torrent.downloading
        """
        return TorrentStatus(self.__getattr__("status"))

    @property
    def stopped(self) -> bool:
        return self.status == TorrentStatus.stopped

    @property
    def check_pending(self) -> bool:
        return self.status == TorrentStatus.check_pending

    @property
    def checking(self) -> bool:
        return self.status == TorrentStatus.checking

    @property
    def download_pending(self) -> bool:
        return self.status == TorrentStatus.download_pending

    @property
    def downloading(self) -> bool:
        return self.status == TorrentStatus.downloading

    @property
    def seed_pending(self) -> bool:
        return self.status == TorrentStatus.seed_pending

    @property
    def seeding(self) -> bool:
        return self.status == TorrentStatus.seeding

    @property
    def rate_download(self) -> int:
        """
        Returns download rate in B/s

        :rtype: int
        """
        return self.__getattr__("rate_download")

    @property
    def rate_upload(self) -> int:
        """
        Returns upload rate in B/s

        :rtype: int
        """
        return self.__getattr__("rate_upload")

    @property
    def hash_string(self) -> str:
        """Returns the info hash of this torrent.

        :raise: AttributeError -- if server don't return this field
        :rtype: int
        """
        return self.__getattr__("hash_string")

    @property
    def progress(self) -> float:
        """
        download progress in percent.

        :rtype: float
        """
        try:
            # https://gist.github.com/jackiekazil/6201722#gistcomment-2788556
            return round((100.0 * self._fields["percent_done"]), 2)
        except KeyError:
            try:
                size = self.size_when_done
                left = self.left_until_done
                return round((100.0 * (size - left) / float(size)), 2)
            except ZeroDivisionError:
                return 0.0

    @property
    def ratio(self) -> float:
        """
        upload/download ratio.

        :rtype: float
        """
        return float(self.__getattr__("uploadRatio"))

    @property
    def eta(self) -> Optional[datetime.timedelta]:
        """
        the "eta" as datetime.timedelta.

        :rtype: datetime.timedelta
        """
        eta = self.__getattr__("eta")
        if eta >= 0:
            return datetime.timedelta(seconds=eta)
        return None

    @property
    def date_active(self) -> datetime.datetime:
        """the attribute ``activityDate`` as ``datetime.datetime`` in **UTC timezone**.

        .. note::

            raw ``activityDate`` value could be ``0`` for never activated torrent,
            therefore it can't always be converted to local timezone.


        :rtype: datetime.datetime
        """
        return datetime.datetime.fromtimestamp(
            self._fields["activity_date"], datetime.timezone.utc
        )

    @property
    def date_added(self) -> datetime.datetime:
        """raw field ``addedDate`` as ``datetime.datetime`` in **local timezone**.

        :rtype: datetime.datetime
        """
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
        """the attribute "doneDate" as datetime.datetime. returns None if "doneDate" is invalid."""
        done_date = self.__getattr__("done_date")
        # Transmission might forget to set doneDate which is initialized to zero,
        # so if doneDate is zero return None
        if done_date == 0:
            return None
        return datetime.datetime.fromtimestamp(done_date).astimezone()

    def format_eta(self) -> str:
        """
        Returns the attribute *eta* formatted as a string.

        * If eta is -1 the result is 'not available'
        * If eta is -2 the result is 'unknown'
        * Otherwise eta is formatted as <days> <hours>:<minutes>:<seconds>.
        """
        eta = self.__getattr__("eta")
        if eta == -1:
            return "not available"
        if eta == -2:
            return "unknown"
        return format_timedelta(datetime.timedelta(seconds=eta))

    @property
    def download_dir(self) -> Optional[str]:
        """The download directory.

        :available: transmission version 1.5.
        :available: RPC version 4.
        """
        return self.__getattr__("download_dir")

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
        return self.__getattr__("peer_limit")

    @property
    def bandwidth_priority(self) -> Priority:
        """
        Bandwidth priority as string.
        """

        return Priority(self.__getattr__("bandwidth_priority"))

    @property
    def seed_idle_limit(self) -> int:
        """
        seed idle limit in minutes.
        """
        return self.__getattr__("seed_idle_limit")

    @property
    def is_finished(self) -> bool:
        """Returns true if the torrent is finished (available from rpc version 2.0)"""
        return self.__getattr__("is_finished")

    @property
    def is_stalled(self) -> bool:
        """Returns true if the torrent is stalled (available from rpc version 2.4)"""
        return self.__getattr__("is_stalled")

    @property
    def size_when_done(self) -> int:
        """Size in bytes when the torrent is done"""
        return self.__getattr__("size_when_done")

    @property
    def total_size(self) -> int:
        """Total size in bytes"""
        return self.__getattr__("total_size")

    @property
    def left_until_done(self) -> int:
        """Bytes left until done"""
        return self.__getattr__("left_until_done")

    @property
    def desired_available(self) -> int:
        """Bytes that are left to download and available"""
        return self.__getattr__("desired_available")

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
        return LimitMode(self.__getattr__("seed_idle_mode"))

    @property
    def seed_ratio_limit(self) -> float:
        """
        Torrent seed ratio limit as float. Also see seed_ratio_mode.
        This is a mutator.

        :rtype: float
        """

        return self.__getattr__("seed_ratio_limit")

    @property
    def seed_ratio_mode(self) -> Priority:
        """
        Seed ratio mode as string. Can be one of 'global', 'single' or 'unlimited'.

         * global, use session seed ratio limit.
         * single, use torrent seed ratio limit. See seed_ratio_limit.
         * unlimited, no seed ratio limit.

        This is a mutator.
        """
        return Priority(self.__getattr__("seed_ratio_mode"))

    @property
    def upload_limit(self) -> int:
        """
        upload limit.
        Can be a number or None.
        """
        return self.__getattr__("upload_limited")

    @property
    def queue_position(self) -> int:
        """queue position for this torrent."""
        return self.__getattr__("queue_position")

    @property
    def activity_date(self) -> int:
        """Last time of upload or download activity."""
        return self.__getattr__("activity_date")

    @property
    def added_date(self) -> int:
        """The date when this torrent was first added."""
        return self.__getattr__("added_date")

    @property
    def comment(self) -> str:
        """Torrent comment."""
        return self.__getattr__("comment")

    @property
    def corrupt_ever(self) -> int:
        """Number of bytes of corrupt data downloaded."""
        return self.__getattr__("corrupt_ever")

    @property
    def creator(self) -> str:
        """Torrent creator."""
        return self.__getattr__("creator")

    @property
    def date_created(self) -> int:
        """Torrent creation date."""
        return self.__getattr__("date_created")

    @property
    def done_date(self) -> int:
        """The date when the torrent finished downloading."""
        return self.__getattr__("done_date")

    @property
    def download_limited(self) -> bool:
        """Download limit is enabled"""
        return self.__getattr__("download_limited")

    @property
    def downloaded_ever(self) -> int:
        """Number of bytes of good data downloaded."""
        return self.__getattr__("downloaded_ever")

    @property
    def edit_date(self) -> int:
        """editDate

        added rpc version 16"""
        return self.__getattr__("edit_date")

    @property
    def error(self) -> int:
        """Kind of error. 0 means OK, 1 means tracker warning, 2 means tracker error, 3 means local error."""
        return self.__getattr__("error")

    @property
    def error_string(self) -> str:
        """Error message."""
        return self.__getattr__("error_string")

    @property
    def eta_idle(self) -> int:
        """Estimated number of seconds left until the idle time limit is reached.
         -1 means not available and -2 means unknown.

        added rpc version 15"""
        return self.__getattr__("eta_idle")

    @property
    def file_stats(self) -> list:
        """Away of file statistics containing bytesCompleted, wanted and priority."""
        return self.__getattr__("file_stats")

    @property
    def have_unchecked(self) -> int:
        """Number of bytes of partial pieces."""
        return self.__getattr__("have_unchecked")

    @property
    def have_valid(self) -> int:
        """Number of bytes of checksum verified data."""
        return self.__getattr__("have_valid")

    @property
    def honors_session_limits(self) -> bool:
        """True if session upload limits are honored"""
        return self.__getattr__("honors_session_limits")

    @property
    def is_private(self) -> bool:
        """True if the torrent is private."""
        return self.__getattr__("is_private")

    @property
    def labels(self) -> list:
        """array of string labels

        added rpc version 16"""
        return self.__getattr__("labels")

    @property
    def magnet_link(self) -> str:
        """The magnet link for this torrent."""
        return self.__getattr__("magnet_link")

    @property
    def manual_announce_time(self) -> int:
        """The time until you manually ask for more peers."""
        return self.__getattr__("manual_announce_time")

    @property
    def max_connected_peers(self) -> int:
        """Maximum of connected peers."""
        return self.__getattr__("max_connected_peers")

    @property
    def metadata_percent_complete(self) -> int:
        """Download progress of metadata. 0.0 to 1.0."""
        return self.__getattr__("metadata_percent_complete")

    @property
    def peers(self) -> list:
        """Array of peer objects."""
        return self.__getattr__("peers")

    @property
    def peers_connected(self) -> int:
        """Number of peers we are connected to."""
        return self.__getattr__("peers_connected")

    @property
    def peers_from(self) -> dict:
        """Object containing download peers counts for different peer types."""
        return self.__getattr__("peers_from")

    @property
    def peers_getting_from_us(self) -> int:
        """Number of peers we are sending data to."""
        return self.__getattr__("peers_getting_from_us")

    @property
    def peers_sending_to_us(self) -> int:
        """Number of peers sending to us"""
        return self.__getattr__("peers_sending_to_us")

    @property
    def percent_done(self) -> int:
        """Download progress of selected files. 0.0 to 1.0."""
        return self.__getattr__("percent_done")

    @property
    def piece_count(self) -> int:
        """Number of pieces."""
        return self.__getattr__("piece_count")

    @property
    def piece_size(self) -> int:
        """Number of bytes in a piece."""
        return self.__getattr__("piece_size")

    @property
    def pieces(self) -> str:
        """String with base64 encoded bitfield indicating finished pieces."""
        return self.__getattr__("pieces")

    @property
    def priorities(self) -> list:
        """Array of file priorities."""
        return self.__getattr__("priorities")

    @property
    def recheck_progress(self) -> int:
        """Progress of recheck. 0.0 to 1.0."""
        return self.__getattr__("recheck_progress")

    @property
    def seconds_downloading(self) -> int:
        """

        added rpc version 15"""
        return self.__getattr__("seconds_downloading")

    @property
    def seconds_seeding(self) -> int:
        """

        added rpc version 15"""
        return self.__getattr__("seconds_seeding")

    @property
    def start_date(self) -> int:
        """The date when the torrent was last started."""
        return self.__getattr__("start_date")

    @property
    def torrent_file(self) -> str:
        """Path to .torrent file."""
        return self.__getattr__("torrent_file")

    @property
    def tracker_stats(self) -> list:
        """Array of object containing tracker statistics."""
        return self.__getattr__("tracker_stats")

    @property
    def trackers(self) -> list:
        """Array of tracker objects."""
        return self.__getattr__("trackers")

    @property
    def upload_limited(self) -> bool:
        """Upload limit enabled."""
        return self.__getattr__("upload_limited")

    @property
    def upload_ratio(self) -> int:
        """Seed ratio."""
        return self.__getattr__("upload_ratio")

    @property
    def uploaded_ever(self) -> int:
        """Number of bytes uploaded, ever."""
        return self.__getattr__("uploaded_ever")

    @property
    def wanted(self) -> list:
        """Array of booleans indicated wanted files."""
        return self.__getattr__("wanted")

    @property
    def webseeds(self) -> list:
        """Array of webseeds objects"""
        return self.__getattr__("webseeds")

    @property
    def webseeds_sending_to_us(self) -> int:
        """Number of webseeds seeding to us."""
        return self.__getattr__("webseeds_sending_to_us")
