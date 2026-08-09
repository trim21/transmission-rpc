from __future__ import annotations

import base64
import enum
from datetime import datetime, timedelta, timezone
from functools import cached_property
from typing import Any

from typing_extensions import deprecated

from transmission_rpc._tracker_list import parse_tracker_list
from transmission_rpc.constants import IdleMode, Priority, RatioLimitMode
from transmission_rpc.types import BitMap, Container, File, get_field
from transmission_rpc.utils import format_timedelta

_STATUS_NEW_MAPPING = {
    0: "stopped",
    1: "check pending",
    2: "checking",
    3: "download pending",
    4: "downloading",
    5: "seed pending",
    6: "seeding",
}


def get_status(code: int) -> str:
    """Get the torrent status using new status codes"""
    return _STATUS_NEW_MAPPING.get(code) or f"unknown status {code}"


class Status(str, enum.Enum):
    """enum for torrent status"""

    STOPPED = "stopped"
    """"""
    CHECK_PENDING = "check pending"
    """"""

    CHECKING = "checking"
    """"""
    DOWNLOAD_PENDING = "download pending"
    """"""

    DOWNLOADING = "downloading"
    """"""

    SEED_PENDING = "seed pending"
    """"""

    SEEDING = "seeding"
    """"""

    @property
    def stopped(self) -> bool:
        """if torrent stopped"""
        return self == "stopped"

    @property
    def check_pending(self) -> bool:
        """if torrent check pending"""
        return self == "check pending"

    @property
    def checking(self) -> bool:
        """if torrent checking"""
        return self == "checking"

    @property
    def download_pending(self) -> bool:
        """if download pending"""
        return self == "download pending"

    @property
    def downloading(self) -> bool:
        """if downloading"""
        return self == "downloading"

    @property
    def seed_pending(self) -> bool:
        """if seed pending"""
        return self == "seed pending"

    @property
    def seeding(self) -> bool:
        """if seeding"""
        return self == "seeding"

    def __str__(self) -> str:
        return self.value


class Peer(Container):
    """
    type for :py:meth:`Torrent.peers`
    """

    @property
    def address(self) -> str:
        return self._get_field("address")

    @property
    def bytes_to_client(self) -> int:
        return self._get_field("bytes_to_client")

    @property
    def bytes_to_peer(self) -> int:
        return self._get_field("bytes_to_peer")

    @property
    def client_name(self) -> str:
        return self._get_field("client_name")

    @property
    def client_is_choked(self) -> bool:
        return self._get_field("client_is_choked")

    @property
    def client_is_interested(self) -> bool:
        return self._get_field("client_is_interested")

    @property
    def flag_str(self) -> str:
        return self._get_field("flag_str")

    @property
    def is_downloading_from(self) -> bool:
        return self._get_field("is_downloading_from")

    @property
    def is_encrypted(self) -> bool:
        return self._get_field("is_encrypted")

    @property
    def is_incoming(self) -> bool:
        return self._get_field("is_incoming")

    @property
    def is_uploading_to(self) -> bool:
        return self._get_field("is_uploading_to")

    @property
    def is_utp(self) -> bool:
        return self._get_field("is_utp")

    @property
    def peer_is_choked(self) -> bool:
        return self._get_field("peer_is_choked")

    @property
    def peer_is_interested(self) -> bool:
        return self._get_field("peer_is_interested")

    @property
    def peer_id(self) -> str:
        return self._get_field("peer_id")

    @property
    def port(self) -> int:
        return self._get_field("port")

    @property
    def progress(self) -> float:
        return self._get_field("progress")

    @property
    def rate_to_client(self) -> float:
        return self._get_field("rate_to_client")

    @property
    def rate_to_peer(self) -> float:
        return self._get_field("rate_to_peer")


class PeersFrom(Container):
    """
    type for :py:meth:`Torrent.peersFrom`
    """

    @property
    def from_cache(self) -> float:
        return self._get_field("from_cache")

    @property
    def from_dht(self) -> float:
        return self._get_field("from_dht")

    @property
    def from_incoming(self) -> float:
        return self._get_field("from_incoming")

    @property
    def from_lpd(self) -> float:
        return self._get_field("from_lpd")

    @property
    def from_ltep(self) -> float:
        return self._get_field("from_ltep")

    @property
    def from_pex(self) -> float:
        return self._get_field("from_pex")

    @property
    def from_tracker(self) -> float:
        return self._get_field("from_tracker")


class FileStat(Container):
    """
    type for :py:meth:`Torrent.file_stats`
    """

    @property
    @deprecated("use `.bytes_completed` instead")
    def bytesCompleted(self) -> int:
        """Compatibility alias for :attr:`bytes_completed`.

        .. deprecated:: 8.0.0
            Use :attr:`bytes_completed` instead.
        """
        return self._get_field("bytes_completed")

    @property
    def bytes_completed(self) -> int:
        return self._get_field("bytes_completed")

    @property
    def wanted(self) -> int:
        return self._get_field("wanted")

    @property
    def priority(self) -> int:
        return self._get_field("priority")


class Tracker(Container):
    """
    type for :py:attr:`Torrent.trackers`
    """

    @property
    def id(self) -> int:
        return self._get_field("id")

    @property
    def announce(self) -> str:
        return self._get_field("announce")

    @property
    def scrape(self) -> str:
        return self._get_field("scrape")

    @property
    def site_name(self) -> str:
        return self._get_field("sitename")

    @property
    def tier(self) -> int:
        return self._get_field("tier")


class TrackerStats(Container):
    """
    type for :py:attr:`Torrent.tracker_stats`
    """

    @property
    def id(self) -> int:
        return self._get_field("id")

    @property
    def announce_state(self) -> int:
        return self._get_field("announce_state")

    @property
    def announce(self) -> str:
        return self._get_field("announce")

    @property
    def download_count(self) -> int:
        return self._get_field("download_count")

    @property
    def downloader_count(self) -> int:
        return self._get_field("downloader_count")

    @property
    def has_announced(self) -> bool:
        return self._get_field("has_announced")

    @property
    def has_scraped(self) -> bool:
        return self._get_field("has_scraped")

    @property
    def host(self) -> str:
        return self._get_field("host")

    @property
    def is_backup(self) -> bool:
        return self._get_field("is_backup")

    @property
    def last_announce_peer_count(self) -> int:
        return self._get_field("last_announce_peer_count")

    @property
    def last_announce_result(self) -> str:
        return self._get_field("last_announce_result")

    @property
    def last_announce_start_time(self) -> int:
        return self._get_field("last_announce_start_time")

    @property
    def last_announce_succeeded(self) -> bool:
        return self._get_field("last_announce_succeeded")

    @property
    def last_announce_time(self) -> int:
        return self._get_field("last_announce_time")

    @property
    def last_announce_timed_out(self) -> bool:
        return self._get_field("last_announce_timed_out")

    @property
    def last_scrape_result(self) -> str:
        return self._get_field("last_scrape_result")

    @property
    def last_scrape_start_time(self) -> int:
        return self._get_field("last_scrape_start_time")

    @property
    def last_scrape_succeeded(self) -> bool:
        return self._get_field("last_scrape_succeeded")

    @property
    def last_scrape_time(self) -> int:
        return self._get_field("last_scrape_time")

    @property
    def last_scrape_timed_out(self) -> bool:
        return self._get_field("last_scrape_timed_out")

    @property
    def leecher_count(self) -> int:
        return self._get_field("leecher_count")

    @property
    def next_announce_time(self) -> int:
        return self._get_field("next_announce_time")

    @property
    def next_scrape_time(self) -> int:
        return self._get_field("next_scrape_time")

    @property
    def scrape_state(self) -> int:
        return self._get_field("scrape_state")

    @property
    def scrape(self) -> str:
        return self._get_field("scrape")

    @property
    def seeder_count(self) -> int:
        return self._get_field("seeder_count")

    @property
    def site_name(self) -> str:
        return self._get_field("sitename")

    @property
    def tier(self) -> int:
        return self._get_field("tier")


class Webseed(Container):
    @property
    def url(self) -> str:
        return self._get_field("url")

    @property
    def is_downloading(self) -> bool:
        return self._get_field("is_downloading")

    @property
    def download_bytes_per_second(self) -> int:
        return self._get_field("download_bytes_per_second")


class Torrent(Container):
    """
    Torrent is a class holding the data received from Transmission regarding a bittorrent transfer.

    Warnings:
        setter on Torrent's properties has been removed, please use :py:meth:`Client.change_torrent` instead
    """

    def __init__(self, *, fields: dict[str, Any]):
        if "id" not in fields:
            raise ValueError(
                "Torrent object requires field 'id', "
                "you need to add 'id' in your 'arguments' when calling 'get_torrent'"
            )

        super().__init__(fields=fields)

    @property
    def id(self) -> int:
        return self._get_field("id")

    @property
    def name(self) -> str:
        return self._get_field("name")

    @property
    @deprecated("use `.hash_string` instead")
    def hashString(self) -> str:
        """Compatibility alias for :attr:`hash_string`.

        .. deprecated:: 8.0.0
            Use :attr:`hash_string` instead.
        """
        return self._get_field("hash_string")

    @property
    def hash_string(self) -> str:
        """Torrent info hash string, can also be used as Torrent ID"""
        return self._get_field("hash_string")

    @property
    def info_hash(self) -> str:
        """Alias of :attr:`hash_string`."""
        return self.hash_string

    @property
    @deprecated("this is a typo, do not use this. use `.info_hash` instead")
    def into_hash(self) -> str:
        """Alias of :attr:`info_hash`."""
        return self.info_hash

    @property
    def available(self) -> float:
        """Availability in percent"""
        bytes_all = self.total_size
        bytes_done = sum(get_field(x, "bytes_completed") for x in self._get_field("file_stats"))
        bytes_avail = self.desired_available + bytes_done
        return float((bytes_avail / bytes_all) * 100 if bytes_all else 0)

    @property
    def availability(self) -> list[int]:
        """
        An array of piece_count numbers representing the number of connected peers
        that have each piece, or -1 if we already have the piece ourselves.

        :available: transmission version 4.0.0.
        :available: RPC version 17.
        """
        return self._get_field("availability")

    @property
    def bandwidth_priority(self) -> Priority:
        """this torrent's bandwidth priority"""
        return Priority(self._get_field("bandwidth_priority"))

    @property
    def comment(self) -> str:
        return self._get_field("comment")

    @property
    def corrupt_ever(self) -> int:
        """
        Byte count of all the corrupt data you've ever downloaded for
        this torrent. If you're on a poisoned torrent, this number can
        grow very large.
        """
        return self._get_field("corrupt_ever")

    @property
    def creator(self) -> str:
        return self._get_field("creator")

    @property
    def date_created(self) -> datetime:
        """
        The date when the torrent file was created (by the torrent creator).
        """
        return datetime.fromtimestamp(self._get_field("date_created"), timezone.utc)

    @property
    def desired_available(self) -> int:
        """
        Byte count of all the piece data we want and don't have yet,
        but that a connected peer does have. [0...leftUntilDone]
        """
        return self._get_field("desired_available")

    @property
    def download_dir(self) -> str:
        """The download directory.

        :available: transmission version 1.5.
        :available: RPC version 4.
        """
        return self._get_field("download_dir")

    @property
    def downloaded_ever(self) -> int:
        """
        Byte count of all the non-corrupt data you've ever downloaded for this torrent.
        If you deleted the files and downloaded a second time, this will be 2*totalSize.
        """
        return self._get_field("downloaded_ever")

    @property
    def download_limit(self) -> int:
        return self._get_field("download_limit")

    @property
    def download_limited(self) -> bool:
        return self._get_field("download_limited")

    @property
    def edit_date(self) -> datetime:
        """
        The last time during this session that a rarely-changing field
        changed -- e.g. any tr_torrent_metainfo field (trackers, filenames, name)
        or download directory. RPC clients can monitor this to know when
        to reload fields that rarely change.
        """
        return datetime.fromtimestamp(self._get_field("edit_date"), timezone.utc)

    @property
    def error(self) -> int:
        """``0`` for fine task, non-zero for error torrent"""
        return self._get_field("error")

    @property
    def error_string(self) -> str:
        """empty string for fine task"""
        return self._get_field("error_string")

    @property
    def eta(self) -> timedelta | None:
        """
        the "eta" as datetime.timedelta.

        If downloading, estimated the ``timedelta`` left until the torrent is done.
        If seeding, estimated the ``timedelta`` left until seed ratio is reached.

        raw `eta` maybe negative:
        - `-1` for ETA Not Available.
        - `-2` for ETA Unknown.

        https://github.com/transmission/transmission/blob/3.00/libtransmission/transmission.h#L1748-L1749
        """
        eta = self._get_field("eta")
        if eta >= 0:
            return timedelta(seconds=eta)

        return None

    @property
    def eta_idle(self) -> timedelta | None:
        """If seeding, number of seconds left until the idle time limit is reached."""
        v = self._get_field("eta_idle")
        if v >= 0:
            return timedelta(seconds=v)
        return None

    @property
    def file_count(self) -> int | None:
        return self._get_field("file_count")

    @property
    def bytes_completed(self) -> list[int]:
        return self._get_field("bytes_completed")

    def get_files(self) -> list[File]:
        """
        Get list of files for this torrent.

        Note:
            The order of the files is guaranteed. The index of file object is the id of the file
            when calling :py:meth:`transmission_rpc.Client.change_torrent`

        .. code-block:: python

            from transmission_rpc import Client

            torrent = Client().get_torrent(0)

            for file in torrent.get_files():
                print(file.id)

        """
        files = self._get_field("files")
        indices = range(len(files))
        priorities: list[Priority | None] = (
            [Priority(v) for v in self._get_field("priorities")] if "priorities" in self.fields else [None] * len(files)
        )
        wanted: list[bool | None] = (
            [bool(v) for v in self._get_field("wanted")] if "wanted" in self.fields else [None] * len(files)
        )
        return [
            File(
                selected=selected,
                priority=priority,
                size=file["length"],
                name=file["name"],
                completed=get_field(file, "bytes_completed"),
                id=id,
                begin_piece=get_field(file, "begin_piece", None),
                end_piece=get_field(file, "end_piece", None),
            )
            for id, file, priority, selected in zip(indices, files, priorities, wanted, strict=False)
        ]

    @property
    def file_stats(self) -> list[FileStat]:
        """file stats"""
        return [FileStat(fields=x) for x in self._get_field("file_stats")]

    @property
    def group(self) -> str:
        return self.get("group", "")

    @property
    def have_unchecked(self) -> int:
        """
        Byte count of all the partial piece data we have for this torrent.
        As pieces become complete,
        this value may decrease as portions of it are moved to "corrupt" or "haveValid".
        """
        return self._get_field("have_unchecked")

    @property
    def have_valid(self) -> int:
        """Byte count of all the checksum-verified data we have for this torrent."""
        return self._get_field("have_valid")

    @property
    def honors_session_limits(self) -> bool:
        """true if session upload limits are honored"""
        return self._get_field("honors_session_limits")

    @property
    def is_finished(self) -> bool:
        return self._get_field("is_finished")

    @property
    def is_private(self) -> bool:
        return self._get_field("is_private")

    @property
    def is_stalled(self) -> bool:
        return self._get_field("is_stalled")

    @property
    def labels(self) -> list[str]:
        return self._get_field("labels")

    @property
    def left_until_done(self) -> int:
        """
        Byte count of how much data is left to be downloaded until we've got
        all the pieces that we want. [0...tr_stat.sizeWhenDone]
        """
        return self._get_field("left_until_done")

    @property
    def magnet_link(self) -> str:
        return self._get_field("magnet_link")

    @property
    def manual_announce_time(self) -> datetime:
        return datetime.fromtimestamp(self._get_field("manual_announce_time"), timezone.utc)

    @property
    def max_connected_peers(self) -> int:
        return self._get_field("max_connected_peers")

    @property
    def metadata_percent_complete(self) -> float:
        """
        How much of the metadata the torrent has.
        For torrents added from a torrent this will always be 1.
        For magnet links, this number will from from 0 to 1 as the metadata is downloaded.
        Range is [0..1]
        """
        return float(self._get_field("metadata_percent_complete"))

    @property
    def peer_limit(self) -> int:
        """maximum number of peers"""
        return self._get_field("peer_limit")

    @property
    def peers(self) -> list[Peer]:
        return [Peer(fields=x) for x in self._get_field("peers")]

    @property
    def peers_connected(self) -> int:
        """Number of peers that we're connected to"""
        return self._get_field("peers_connected")

    @property
    def peers_from(self) -> PeersFrom:
        """How many peers we found out about from the tracker, or from pex,
        or from incoming connections, or from our resume file."""
        return PeersFrom(fields=self._get_field("peers_from"))

    @property
    def peers_getting_from_us(self) -> int:
        """Number of peers that we're sending data to"""
        return self._get_field("peers_getting_from_us")

    @property
    def peers_sending_to_us(self) -> int:
        """Number of peers that are sending data to us."""
        return self._get_field("peers_sending_to_us")

    @property
    def percent_complete(self) -> float:
        """How much has been downloaded of the entire torrent. Range is [0..1]"""
        return float(self._get_field("percent_complete"))

    @property
    def percent_done(self) -> float:
        """
        How much has been downloaded of the files the user wants. This differs
        from percentComplete if the user wants only some of the torrent's files.
        Range is [0..1]
        """
        return float(self._get_field("percent_done"))

    @cached_property
    def pieces(self) -> BitMap:
        return BitMap(base64.b64decode(self._get_field("pieces").encode()))

    @property
    def piece_count(self) -> int:
        return self._get_field("piece_count")

    @property
    def piece_size(self) -> int:
        return self._get_field("piece_size")

    @property
    def priorities(self) -> list[Priority]:
        """
        A list of bandwidth priorities for each file in the torrent.
        """
        return [Priority(x) for x in self._get_field("priorities")]

    @property
    def primary_mime_type(self) -> str:
        return self._get_field("primary_mime_type")

    @property
    def queue_position(self) -> int:
        """position of this torrent in its queue [0...n)"""
        return self._get_field("queue_position")

    @property
    def rate_download(self) -> int:
        """download rate (B/s)"""
        return self._get_field("rate_download")

    @property
    def rate_upload(self) -> int:
        """upload rate (B/s)"""
        return self._get_field("rate_upload")

    @property
    def recheck_progress(self) -> float:
        return float(self._get_field("recheck_progress"))

    @property
    def seconds_downloading(self) -> int:
        """Cumulative seconds the torrent's ever spent downloading"""
        return self._get_field("seconds_downloading")

    @property
    def seconds_seeding(self) -> int:
        """Cumulative seconds the torrent's ever spent seeding"""
        return self._get_field("seconds_seeding")

    @property
    def seed_idle_limit(self) -> int:
        return self._get_field("seed_idle_limit")

    @property
    def seed_idle_mode(self) -> IdleMode:
        """
        Seed idle mode as string. Can be one of 'global', 'single' or 'unlimited'.

         * global, use session seed idle limit.
         * single, use torrent seed idle limit. See seed_idle_limit.
         * unlimited, no seed idle limit.
        """
        return IdleMode(self._get_field("seed_idle_mode"))

    @property
    def size_when_done(self) -> int:
        """byte count of all the wanted data"""
        return self._get_field("size_when_done")

    @property
    def trackers(self) -> list[Tracker]:
        """trackers of torrent"""
        return [Tracker(fields=x) for x in self._get_field("trackers")]

    @property
    def tracker_list(self) -> list[list[str]]:
        """Announce URLs grouped by tracker tier.

        Each inner list contains the trackers in one tier.

        .. versionchanged:: 8.0.0
            Earlier versions returned a flat list and discarded tier boundaries.
            Flatten the tiered result explicitly when tier information is not needed:
            ``[url for tier in torrent.tracker_list for url in tier]``.
        """
        return parse_tracker_list(self._get_field("tracker_list"))

    @property
    def tracker_stats(self) -> list[TrackerStats]:
        """tracker status, for example, announce success/failure status"""
        return [TrackerStats(fields=x) for x in self._get_field("tracker_stats")]

    @property
    def total_size(self) -> int:
        return self._get_field("total_size")

    @property
    def torrent_file(self) -> str:
        """
        torrent file location on transmission server

        Examples
        --------
        /var/lib/transmission-daemon/.config/transmission-daemon/torrents/00000000000000000000000000.torrent
        """
        return self._get_field("torrent_file")

    @property
    def uploaded_ever(self) -> int:
        return self._get_field("uploaded_ever")

    @property
    def upload_limit(self) -> int:
        return self._get_field("upload_limit")

    @property
    def upload_limited(self) -> bool:
        return self._get_field("upload_limited")

    @property
    def upload_ratio(self) -> float:
        return float(self._get_field("upload_ratio"))

    @property
    def wanted(self) -> list[int]:
        """if files are wanted, sorted by file index. 1 for wanted 0 for unwanted"""
        return self._get_field("wanted")

    @property
    def webseeds(self) -> list[str]:
        return self._get_field("webseeds")

    @property
    def webseeds_sending_to_us(self) -> int:
        """Number of webseeds that are sending data to us."""
        return self._get_field("webseeds_sending_to_us")

    @property
    def _status(self) -> int:
        """Get the torrent status"""
        return self._get_field("status")

    @property
    def _status_str(self) -> str:
        """Get the torrent status"""
        return get_status(self._get_field("status"))

    @property
    def status(self) -> Status:
        """
        Returns the torrent status. Is either one of 'check pending', 'checking',
        'downloading', 'download pending', 'seeding', 'seed pending' or 'stopped'.
        The first two is related to verification.

        Examples:

        .. code-block:: python

            torrent = Torrent()
            torrent.status.downloading
            torrent.status == 'downloading'

        """
        return Status(self._status_str)

    @property
    def stopped(self) -> bool:
        return self._status == 0

    @property
    def check_pending(self) -> bool:
        return self._status == 1

    @property
    def checking(self) -> bool:
        return self._status == 2

    @property
    def download_pending(self) -> bool:
        return self._status == 3

    @property
    def downloading(self) -> bool:
        return self._status == 4

    @property
    def seed_pending(self) -> bool:
        return self._status == 5

    @property
    def seeding(self) -> bool:
        return self._status == 6

    @property
    def progress(self) -> float:
        """
        download progress in percent.
        """
        try:
            # https://gist.github.com/jackiekazil/6201722#gistcomment-2788556
            return round((100.0 * self._get_field("percent_done")), 2)
        except KeyError:
            try:
                size = self._get_field("size_when_done")
                left = self._get_field("left_until_done")
                return round((100.0 * (size - left) / float(size)), 2)
            except ZeroDivisionError:
                return 0.0

    @property
    def ratio(self) -> float:
        """
        upload/download ratio.
        """
        return float(self._get_field("upload_ratio"))

    @property
    def activity_date(self) -> datetime:
        """
        The last time we uploaded or downloaded piece data on this torrent.
        the attribute ``activityDate`` as ``datetime.datetime`` in **UTC timezone**.

        .. note::

            raw ``activityDate`` value could be ``0`` for never activated torrent,
            therefore it can't always be converted to local timezone.
        """

        return datetime.fromtimestamp(self._get_field("activity_date"), timezone.utc)

    @property
    def added_date(self) -> datetime:
        """When the torrent was first added."""
        return datetime.fromtimestamp(self._get_field("added_date"), timezone.utc)

    @property
    def start_date(self) -> datetime:
        """raw field ``startDate`` as ``datetime.datetime`` in **utc timezone**."""
        return datetime.fromtimestamp(self._get_field("start_date"), timezone.utc)

    @property
    def done_date(self) -> datetime | None:
        """the attribute "doneDate" as datetime.datetime. returns None if "doneDate" is invalid."""
        done_date = self._get_field("done_date")
        # Transmission might forget to set doneDate which is initialized to zero,
        # so if doneDate is zero return None
        if done_date == 0:
            return None
        return datetime.fromtimestamp(done_date, timezone.utc)

    def format_eta(self) -> str:
        """
        Returns the attribute *eta* formatted as a string.

        * If eta is -1 the result is 'not available'
        * If eta is -2 the result is 'unknown'
        * Otherwise eta is formatted as <days> <hours>:<minutes>:<seconds>.
        """
        eta = self._get_field("eta")
        if eta == -1:
            return "not available"
        if eta == -2:
            return "unknown"
        return format_timedelta(timedelta(seconds=eta))

    @property
    def priority(self) -> Priority:
        """
        Bandwidth priority as string.
        Can be one of 'low', 'normal', 'high'. This is a mutator.
        """

        return Priority(self._get_field("bandwidth_priority"))

    @property
    def seed_ratio_limit(self) -> float:
        """
        Torrent seed ratio limit as float. Also see seed_ratio_mode.
        This is a mutator.
        """

        return float(self._get_field("seed_ratio_limit"))

    @property
    def seed_ratio_mode(self) -> RatioLimitMode:
        """
        Seed ratio mode as string. Can be one of 'global', 'single' or 'unlimited'.

         * global, use session seed ratio limit.
         * single, use torrent seed ratio limit. See seed_ratio_limit.
         * unlimited, no seed ratio limit.
        """
        return RatioLimitMode(self._get_field("seed_ratio_mode"))

    @property
    def sequential_download(self) -> bool:
        """
        download torrent pieces sequentially

        added in Transmission 4.1.0 (rpc-version-semver 6.0.0, rpc-version: 18)
        """
        return self._get_field("sequential_download")

    @property
    def sequential_download_from_piece(self) -> int:
        return self._get_field("sequential_download_from_piece")

    @property
    def webseeds_ex(self) -> list[Webseed]:
        return [Webseed(fields=item) for item in self._get_field("webseeds_ex")]

    def __repr__(self) -> str:
        return f"<transmission_rpc.Torrent hashString={self.hash_string!r}>"

    def __str__(self) -> str:
        return f"<transmission_rpc.Torrent {self.name!r}>"
