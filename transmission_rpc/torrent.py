from __future__ import annotations

import base64
import enum
from datetime import datetime, timedelta, timezone
from functools import cached_property
from typing import Any

from typing_extensions import deprecated

from transmission_rpc.constants import IdleMode, Priority, RatioLimitMode
from transmission_rpc.types import BitMap, Container, File
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
        return self.fields["address"]

    @property
    def client_name(self) -> str:
        return self.fields["clientName"]

    @property
    def client_is_choked(self) -> bool:
        return self.fields["clientIsChoked"]

    @property
    def client_is_interested(self) -> bool:
        return self.fields["clientIsInterested"]

    @property
    def flag_str(self) -> str:
        return self.fields["flagStr"]

    @property
    def is_downloading_from(self) -> bool:
        return self.fields["isDownloadingFrom"]

    @property
    def is_encrypted(self) -> bool:
        return self.fields["isEncrypted"]

    @property
    def is_incoming(self) -> bool:
        return self.fields["isIncoming"]

    @property
    def is_uploading_to(self) -> bool:
        return self.fields["isUploadingTo"]

    @property
    def is_utp(self) -> bool:
        return self.fields["isUTP"]

    @property
    def peer_is_choked(self) -> bool:
        return self.fields["peerIsChoked"]

    @property
    def peer_is_interested(self) -> bool:
        return self.fields["peerIsInterested"]

    @property
    def port(self) -> int:
        return self.fields["port"]

    @property
    def progress(self) -> float:
        return self.fields["progress"]

    @property
    def rate_to_client(self) -> float:
        return self.fields["rateToClient"]

    @property
    def rate_to_peer(self) -> float:
        return self.fields["rateToPeer"]


class PeersFrom(Container):
    """
    type for :py:meth:`Torrent.peersFrom`
    """

    @property
    def from_cache(self) -> float:
        return self.fields["fromCache"]

    @property
    def from_dht(self) -> float:
        return self.fields["fromDht"]

    @property
    def from_incoming(self) -> float:
        return self.fields["fromIncoming"]

    @property
    def from_lpd(self) -> float:
        return self.fields["fromLpd"]

    @property
    def from_ltep(self) -> float:
        return self.fields["fromLtep"]

    @property
    def from_pex(self) -> float:
        return self.fields["fromPex"]

    @property
    def from_tracker(self) -> float:
        return self.fields["fromTracker"]


class FileStat(Container):
    """
    type for :py:meth:`Torrent.file_stats`
    """

    @property
    def bytesCompleted(self) -> int:
        return self.fields["bytesCompleted"]

    @property
    def wanted(self) -> int:
        return self.fields["wanted"]

    @property
    def priority(self) -> int:
        return self.fields["priority"]


class Tracker(Container):
    """
    type for :py:attr:`Torrent.trackers`
    """

    @property
    def id(self) -> int:
        return self.fields["id"]

    @property
    def announce(self) -> str:
        return self.fields["announce"]

    @property
    def scrape(self) -> str:
        return self.fields["scrape"]

    @property
    def tier(self) -> int:
        return self.fields["tier"]


class TrackerStats(Container):
    """
    type for :py:attr:`Torrent.tracker_stats`
    """

    @property
    def id(self) -> int:
        return self.fields["id"]

    @property
    def announce_state(self) -> int:
        return self.fields["announceState"]

    @property
    def announce(self) -> str:
        return self.fields["announce"]

    @property
    def download_count(self) -> int:
        return self.fields["downloadCount"]

    @property
    def has_announced(self) -> bool:
        return self.fields["hasAnnounced"]

    @property
    def has_scraped(self) -> bool:
        return self.fields["hasScraped"]

    @property
    def host(self) -> str:
        return self.fields["host"]

    @property
    def is_backup(self) -> bool:
        return self.fields["isBackup"]

    @property
    def last_announce_peer_count(self) -> int:
        return self.fields["lastAnnouncePeerCount"]

    @property
    def last_announce_result(self) -> str:
        return self.fields["lastAnnounceResult"]

    @property
    def last_announce_start_time(self) -> int:
        return self.fields["lastAnnounceStartTime"]

    @property
    def last_announce_succeeded(self) -> bool:
        return self.fields["lastAnnounceSucceeded"]

    @property
    def last_announce_time(self) -> int:
        return self.fields["lastAnnounceTime"]

    @property
    def last_announce_timed_out(self) -> bool:
        return self.fields["lastAnnounceTimedOut"]

    @property
    def last_scrape_result(self) -> str:
        return self.fields["lastScrapeResult"]

    @property
    def last_scrape_start_time(self) -> int:
        return self.fields["lastScrapeStartTime"]

    @property
    def last_scrape_succeeded(self) -> bool:
        return self.fields["lastScrapeSucceeded"]

    @property
    def last_scrape_time(self) -> int:
        return self.fields["lastScrapeTime"]

    @property
    def last_scrape_timed_out(self) -> bool:
        return self.fields["lastScrapeTimedOut"]

    @property
    def leecher_count(self) -> int:
        return self.fields["leecherCount"]

    @property
    def next_announce_time(self) -> int:
        return self.fields["nextAnnounceTime"]

    @property
    def next_scrape_time(self) -> int:
        return self.fields["nextScrapeTime"]

    @property
    def scrape_state(self) -> int:
        return self.fields["scrapeState"]

    @property
    def scrape(self) -> str:
        return self.fields["scrape"]

    @property
    def seeder_count(self) -> int:
        return self.fields["seederCount"]

    @property
    def site_name(self) -> str:
        return self.fields["sitename"]

    @property
    def tier(self) -> int:
        return self.fields["tier"]


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
        return self.fields["id"]

    @property
    def name(self) -> str:
        return self.fields["name"]

    @property
    def hashString(self) -> str:
        """Torrent info hash string, can also be used as Torrent ID"""
        return self.fields["hashString"]

    @property
    def hash_string(self) -> str:
        """Torrent info hash string, can also be used as Torrent ID"""
        return self.fields["hashString"]

    @property
    def info_hash(self) -> str:
        """alias of ``hashString``"""
        return self.hashString

    @property
    @deprecated("this is a typo, do not use this. use `.info_hash` instead")
    def into_hash(self) -> str:
        """alias of ``hashString``"""
        return self.hashString

    @property
    def available(self) -> float:
        """Availability in percent"""
        bytes_all = self.total_size
        bytes_done = sum(x["bytesCompleted"] for x in self.fields["fileStats"])
        bytes_avail = self.desired_available + bytes_done
        return float((bytes_avail / bytes_all) * 100 if bytes_all else 0)

    # @property
    # def availability(self) -> list:
    #     """TODO"""
    # return self.fields["availability"]

    @property
    def bandwidth_priority(self) -> Priority:
        """this torrent's bandwidth priority"""
        return Priority(self.fields["bandwidthPriority"])

    @property
    def comment(self) -> str:
        return self.fields["comment"]

    @property
    def corrupt_ever(self) -> int:
        """
        Byte count of all the corrupt data you've ever downloaded for
        this torrent. If you're on a poisoned torrent, this number can
        grow very large.
        """
        return self.fields["corruptEver"]

    @property
    def creator(self) -> str:
        return self.fields["creator"]

    # TODO
    # @property
    # def date_created(self):
    #     return self.fields["dateCreated"]

    @property
    def desired_available(self) -> int:
        """
        Byte count of all the piece data we want and don't have yet,
        but that a connected peer does have. [0...leftUntilDone]
        """
        return self.fields["desiredAvailable"]

    @property
    def download_dir(self) -> str:
        """The download directory.

        :available: transmission version 1.5.
        :available: RPC version 4.
        """
        return self.fields["downloadDir"]

    @property
    def downloaded_ever(self) -> int:
        """
        Byte count of all the non-corrupt data you've ever downloaded for this torrent.
        If you deleted the files and downloaded a second time, this will be 2*totalSize.
        """
        return self.fields["downloadedEver"]

    @property
    def download_limit(self) -> int:
        return self.fields["downloadLimit"]

    @property
    def download_limited(self) -> bool:
        return self.fields["downloadLimited"]

    @property
    def edit_date(self) -> datetime:
        """
        The last time during this session that a rarely-changing field
        changed -- e.g. any tr_torrent_metainfo field (trackers, filenames, name)
        or download directory. RPC clients can monitor this to know when
        to reload fields that rarely change.
        """
        return datetime.fromtimestamp(self.fields["editDate"], timezone.utc)

    @property
    def error(self) -> int:
        """``0`` for fine task, non-zero for error torrent"""
        return self.fields["error"]

    @property
    def error_string(self) -> str:
        """empty string for fine task"""
        return self.fields["errorString"]

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
        eta = self.fields["eta"]
        if eta >= 0:
            return timedelta(seconds=eta)

        return None

    @property
    def eta_idle(self) -> timedelta | None:
        v = self.fields["etaIdle"]
        if v >= 0:
            return timedelta(seconds=v)
        return None

    @property
    def file_count(self) -> int | None:
        return self.fields["file-count"]

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
        files = self.fields["files"]
        indices = range(len(files))
        priorities: list[Priority | None] = (
            [Priority(v) for v in self.fields["priorities"]] if "priorities" in self.fields else [None] * len(files)
        )
        wanted: list[bool | None] = (
            [bool(v) for v in self.fields["wanted"]] if "wanted" in self.fields else [None] * len(files)
        )
        return [
            File(
                selected=selected,
                priority=priority,
                size=file["length"],
                name=file["name"],
                completed=file["bytesCompleted"],
                id=id,
                begin_piece=file.get("begin_piece"),
                end_piece=file.get("end_piece"),
            )
            for id, file, priority, selected in zip(indices, files, priorities, wanted)
        ]

    @property
    def file_stats(self) -> list[FileStat]:
        """file stats"""
        return [FileStat(fields=x) for x in self.fields["fileStats"]]

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
        return self.fields["haveUnchecked"]

    @property
    def have_valid(self) -> int:
        """Byte count of all the checksum-verified data we have for this torrent."""
        return self.fields["haveValid"]

    @property
    def honors_session_limits(self) -> bool:
        """true if session upload limits are honored"""
        return self.fields["honorsSessionLimits"]

    @property
    def is_finished(self) -> bool:
        return self.fields["isFinished"]

    @property
    def is_private(self) -> bool:
        return self.fields["isPrivate"]

    @property
    def is_stalled(self) -> bool:
        return self.fields["isStalled"]

    @property
    def labels(self) -> list[str]:
        return self.fields["labels"]

    @property
    def left_until_done(self) -> int:
        """
        Byte count of how much data is left to be downloaded until we've got
        all the pieces that we want. [0...tr_stat.sizeWhenDone]
        """
        return self.fields["leftUntilDone"]

    @property
    def magnet_link(self) -> str:
        return self.fields["magnetLink"]

    @property
    def manual_announce_time(self) -> datetime:
        return datetime.fromtimestamp(self.fields["manualAnnounceTime"], timezone.utc)

    @property
    def max_connected_peers(self) -> int:
        return self.fields["maxConnectedPeers"]

    @property
    def metadata_percent_complete(self) -> float:
        """
        How much of the metadata the torrent has.
        For torrents added from a torrent this will always be 1.
        For magnet links, this number will from from 0 to 1 as the metadata is downloaded.
        Range is [0..1]
        """
        return float(self.fields["metadataPercentComplete"])

    @property
    def peer_limit(self) -> int:
        """maximum number of peers"""
        return self.fields["peer-limit"]

    @property
    def peers(self) -> list[Peer]:
        return [Peer(fields=x) for x in self.fields["peers"]]

    @property
    def peers_connected(self) -> int:
        """Number of peers that we're connected to"""
        return self.fields["peersConnected"]

    @property
    def peers_from(self) -> PeersFrom:
        """How many peers we found out about from the tracker, or from pex,
        or from incoming connections, or from our resume file."""
        return PeersFrom(fields=self.fields["peersFrom"])

    @property
    def peers_getting_from_us(self) -> int:
        """Number of peers that we're sending data to"""
        return self.fields["peersGettingFromUs"]

    @property
    def peers_sending_to_us(self) -> int:
        """Number of peers that are sending data to us."""
        return self.fields["peersSendingToUs"]

    @property
    def percent_complete(self) -> float:
        """How much has been downloaded of the entire torrent. Range is [0..1]"""
        return float(self.fields["percentComplete"])

    @property
    def percent_done(self) -> float:
        """
        How much has been downloaded of the files the user wants. This differs
        from percentComplete if the user wants only some of the torrent's files.
        Range is [0..1]
        """
        return float(self.fields["percentDone"])

    @cached_property
    def pieces(self) -> BitMap:
        return BitMap(base64.b64decode(self.fields["pieces"].encode()))

    @property
    def piece_count(self) -> int:
        return self.fields["pieceCount"]

    @property
    def piece_size(self) -> int:
        return self.fields["pieceSize"]

    # TODO
    # @property
    # def priorities(self):
    #     return self.fields["priorities"]

    @property
    def primary_mime_type(self) -> str:
        return self.fields["primary-mime-type"]

    @property
    def queue_position(self) -> int:
        """position of this torrent in its queue [0...n)"""
        return self.fields["queuePosition"]

    @property
    def rate_download(self) -> int:
        """download rate (B/s)"""
        return self.fields["rateDownload"]

    @property
    def rate_upload(self) -> int:
        """upload rate (B/s)"""
        return self.fields["rateUpload"]

    @property
    def recheck_progress(self) -> float:
        return float(self.fields["recheckProgress"])

    @property
    def seconds_downloading(self) -> int:
        return self.fields["secondsDownloading"]

    @property
    def seconds_seeding(self) -> int:
        return self.fields["secondsSeeding"]

    @property
    def seed_idle_limit(self) -> int:
        return self.fields["seedIdleLimit"]

    # @property
    # def seed_idle_mode(self) -> int:
    #     """	which seeding inactivity to use. See tr_idlelimit"""
    #     return self.fields["seedIdleMode"]

    @property
    def size_when_done(self) -> int:
        return self.fields["sizeWhenDone"]

    @property
    def trackers(self) -> list[Tracker]:
        """trackers of torrent"""
        return [Tracker(fields=x) for x in self.fields["trackers"]]

    @property
    def tracker_list(self) -> list[str]:
        """list of str of announce URLs"""
        return [x for x in self.fields["trackerList"].splitlines() if x]

    @property
    def tracker_stats(self) -> list[TrackerStats]:
        """tracker status, for example, announce success/failure status"""
        return [TrackerStats(fields=x) for x in self.fields["trackerStats"]]

    @property
    def total_size(self) -> int:
        return self.fields["totalSize"]

    @property
    def torrent_file(self) -> str:
        """
        torrent file location on transmission server

        Examples
        --------
        /var/lib/transmission-daemon/.config/transmission-daemon/torrents/00000000000000000000000000.torrent
        """
        return self.fields["torrentFile"]

    @property
    def uploaded_ever(self) -> int:
        return self.fields["uploadedEver"]

    @property
    def upload_limit(self) -> int:
        return self.fields["uploadLimit"]

    @property
    def upload_limited(self) -> bool:
        return self.fields["uploadLimited"]

    @property
    def upload_ratio(self) -> float:
        return float(self.fields["uploadRatio"])

    @property
    def wanted(self) -> list[int]:
        """if files are wanted, sorted by file index. 1 for wanted 0 for unwanted"""
        return self.fields["wanted"]

    @property
    def webseeds(self) -> list[str]:
        return self.fields["webseeds"]

    @property
    def webseeds_sending_to_us(self) -> int:
        """Number of webseeds that are sending data to us."""
        return self.fields["webseedsSendingToUs"]

    @property
    def _status(self) -> int:
        """Get the torrent status"""
        return self.fields["status"]

    @property
    def _status_str(self) -> str:
        """Get the torrent status"""
        return get_status(self.fields["status"])

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
            return round((100.0 * self.fields["percentDone"]), 2)
        except KeyError:
            try:
                size = self.fields["sizeWhenDone"]
                left = self.fields["leftUntilDone"]
                return round((100.0 * (size - left) / float(size)), 2)
            except ZeroDivisionError:
                return 0.0

    @property
    def ratio(self) -> float:
        """
        upload/download ratio.
        """
        return float(self.fields["uploadRatio"])

    @property
    def activity_date(self) -> datetime:
        """
        The last time we uploaded or downloaded piece data on this torrent.
        the attribute ``activityDate`` as ``datetime.datetime`` in **UTC timezone**.

        .. note::

            raw ``activityDate`` value could be ``0`` for never activated torrent,
            therefore it can't always be converted to local timezone.
        """

        return datetime.fromtimestamp(self.fields["activityDate"], timezone.utc)

    @property
    def added_date(self) -> datetime:
        """When the torrent was first added."""
        return datetime.fromtimestamp(self.fields["addedDate"], timezone.utc)

    @property
    def start_date(self) -> datetime:
        """raw field ``startDate`` as ``datetime.datetime`` in **utc timezone**."""
        return datetime.fromtimestamp(self.fields["startDate"], timezone.utc)

    @property
    def done_date(self) -> datetime | None:
        """the attribute "doneDate" as datetime.datetime. returns None if "doneDate" is invalid."""
        done_date = self.fields["doneDate"]
        # Transmission might forget to set doneDate which is initialized to zero,
        # so if doneDate is zero return None
        if done_date == 0:
            return None
        return datetime.fromtimestamp(done_date).astimezone()

    def format_eta(self) -> str:
        """
        Returns the attribute *eta* formatted as a string.

        * If eta is -1 the result is 'not available'
        * If eta is -2 the result is 'unknown'
        * Otherwise eta is formatted as <days> <hours>:<minutes>:<seconds>.
        """
        eta = self.fields["eta"]
        if eta == -1:
            return "not available"
        if eta == -2:
            return "unknown"
        return format_timedelta(timedelta(seconds=eta))

    # @property
    # def download_limit(self) -> Optional[int]:
    #     """The download limit.
    #
    #     Can be a number or None.
    #     """
    #     if self.fields["downloadLimited"]:
    #         return self.fields["downloadLimit"]
    #     return None

    @property
    def priority(self) -> Priority:
        """
        Bandwidth priority as string.
        Can be one of 'low', 'normal', 'high'. This is a mutator.
        """

        return Priority(self.fields["bandwidthPriority"])

    @property
    def seed_idle_mode(self) -> IdleMode:
        """
        Seed idle mode as string. Can be one of 'global', 'single' or 'unlimited'.

         * global, use session seed idle limit.
         * single, use torrent seed idle limit. See seed_idle_limit.
         * unlimited, no seed idle limit.
        """
        return IdleMode(self.fields["seedIdleMode"])

    @property
    def seed_ratio_limit(self) -> float:
        """
        Torrent seed ratio limit as float. Also see seed_ratio_mode.
        This is a mutator.
        """

        return float(self.fields["seedRatioLimit"])

    @property
    def seed_ratio_mode(self) -> RatioLimitMode:
        """
        Seed ratio mode as string. Can be one of 'global', 'single' or 'unlimited'.

         * global, use session seed ratio limit.
         * single, use torrent seed ratio limit. See seed_ratio_limit.
         * unlimited, no seed ratio limit.
        """
        return RatioLimitMode(self.fields["seedRatioMode"])

    @property
    def sequential_download(self) -> bool:
        """
        download torrent pieces sequentially

        add in Transmission 4.1.0 (rpc-version-semver 5.4.0, rpc-version: 18)
        """
        return self.fields["sequential_download"]

    def __repr__(self) -> str:
        return f"<transmission_rpc.Torrent hashString={self.hashString!r}>"

    def __str__(self) -> str:
        return f"<transmission_rpc.Torrent {self.name!r}>"
