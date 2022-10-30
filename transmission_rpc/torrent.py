import dataclasses
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from transmission_rpc.utils import format_timedelta
from transmission_rpc.constants import PRIORITY, IDLE_LIMIT, RATIO_LIMIT
from transmission_rpc.lib_types import File, Container

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
    return _STATUS_NEW_MAPPING[code]


class Status(str):
    """A wrapped ``str`` for torrent status.

    returned by :py:attr:`.Torrent.status`
    """

    stopped: bool
    check_pending: bool
    checking: bool
    download_pending: bool
    downloading: bool
    seed_pending: bool
    seeding: bool

    def __new__(cls, raw: str) -> "Status":
        obj = super().__new__(cls, raw)
        for status in _STATUS_NEW_MAPPING.values():
            setattr(obj, status.replace(" ", "_"), raw == status)
        return obj


@dataclasses.dataclass(frozen=True)
class FileStat:
    bytesCompleted: int
    wanted: int
    priority: int


@dataclasses.dataclass(frozen=True)
class Tracker:
    id: int
    announce: str
    scrape: str
    tier: int


@dataclasses.dataclass(frozen=True)
class TrackerStats:
    announceState: int
    announce: str
    downloadCount: int
    hasAnnounced: bool
    hasScraped: bool
    host: str
    id: int
    isBackup: bool
    lastAnnouncePeerCount: int
    lastAnnounceResult: str
    lastAnnounceStartTime: int
    lastAnnounceSucceeded: bool
    lastAnnounceTime: int
    lastAnnounceTimedOut: bool
    lastScrapeResult: str
    lastScrapeStartTime: int
    lastScrapeSucceeded: bool
    lastScrapeTime: int
    lastScrapeTimedOut: bool
    leecherCount: int
    nextAnnounceTime: int
    nextScrapeTime: int
    scrapeState: int
    scrape: str
    seederCount: int
    sitename: str
    tier: int


class Torrent(Container):
    """
    Torrent is a dataclasses holding the data received from Transmission regarding a bittorrent transfer.
    """

    def __init__(self, fields: dict):
        self.fields = fields

    @property
    def id(self) -> int:
        return self.fields["id"]

    @property
    def name(self) -> str:
        return self.fields["name"]

    @property
    def hashString(self) -> str:
        return self.fields["hashString"]

    @property
    def activity_date(self) -> datetime:
        """The last time we uploaded or downloaded piece data on this torrent."""
        return datetime.fromtimestamp(self.fields["activityDate"], timezone.utc)

    @property
    def added_date(self) -> datetime:
        """When the torrent was first added."""
        return datetime.fromtimestamp(self.fields["addedDate"], timezone.utc)

    @property
    def available(self) -> float:
        """Availability in percent"""
        bytes_all = self.total_size
        bytes_done = sum(x["bytesCompleted"] for x in self.fields["fileStats"])
        bytes_avail = self.desired_available + bytes_done
        return (bytes_avail / bytes_all) * 100 if bytes_all else 0

    # @property
    # def availability(self) -> list:
    #     """TODO"""
    # return self.fields["availability"]

    @property
    def bandwidth_priority(self) -> int:
        """TODO
        An array of pieceCount numbers representing the number of connected peers that have each piece,
        or -1 if we already have the piece ourselves.
        """
        return self.fields["bandwidthPriority"]

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

    @property
    def date_created(self):
        return self.fields["dateCreated"]

    @property
    def desired_available(self) -> int:
        """
        Byte count of all the piece data we want and don't have yet,
        but that a connected peer does have. [0...leftUntilDone]
        """
        return self.fields["desiredAvailable"]

    @property
    def done_date(self) -> datetime:
        """When the torrent finished downloading."""
        return datetime.fromtimestamp(self.fields["doneDate"], timezone.utc)

    @property
    def download_dir(self) -> Optional[str]:
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
    def eta(self) -> Optional[timedelta]:
        """
        the "eta" as datetime.timedelta.

        If downloading, estimated the ``timedelta`` left until the torrent is done.
        If seeding, estimated the ``timedelta`` left until seed ratio is reached.

        raw `eta` maybe negative:
        - `-1` for ETA Not Available.
        - `-2` for ETA Unknown.

        https://github.com/transmission/transmission/blob/3.00/libtransmission/transmission.h#L1748-L1749

        :rtype: datetime.timedelta
        :raise ValueError: non positive ETA.
        """
        eta = self.fields["eta"]
        if eta >= 0:
            return timedelta(seconds=eta)

    @property
    def eta_idle(self) -> Optional[timedelta]:
        v = self.fields["etaIdle"]
        if v >= 0:
            return timedelta(seconds=v)

    @property
    def file_count(self) -> Optional[int]:
        return self.fields["file-count"]

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
        if "files" in self.fields:
            files = self.fields["files"]
            indices = range(len(files))
            priorities = self.fields["priorities"]
            wanted = self.fields["wanted"]
            for item in zip(indices, files, priorities, wanted):
                result.append(
                    File(
                        selected=bool(item[3]),
                        priority=PRIORITY[item[2]],
                        size=item[1]["length"],
                        name=item[1]["name"],
                        completed=item[1]["bytesCompleted"],
                    )
                )
        return result

    @property
    def file_stats(self) -> List[FileStat]:
        return [FileStat(**x) for x in self.fields["fileStats"]]

    @property
    def group(self) -> str:
        return self.get("group", "")

    @property
    def have_unchecked(self) -> int:
        """
        Byte count of all the partial piece data we have for this torrent.
        As pieces become complete, this value may decrease as portions of it
        are moved to `corrupt' or `haveValid'.
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
    def labels(self) -> str:
        return self.fields["labels"]

    @property
    def left_until_done(self):
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
        return self.fields["metadataPercentComplete"]

    @property
    def peer_limit(self) -> int:
        """maximum number of peers"""
        return self.fields["peer-limit"]

    @property
    def peers(self) -> int:
        return self.fields["peers"]

    @property
    def peers_connected(self) -> int:
        """Number of peers that we're connected to"""
        return self.fields["peersConnected"]

    @property
    def peers_from(self) -> int:
        """How many peers we found out about from the tracker, or from pex,
        or from incoming connections, or from our resume file."""
        return self.fields["peersFrom"]

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
        return self.fields["percentComplete"]

    @property
    def percent_done(self) -> float:
        """
        How much has been downloaded of the files the user wants. This differs
        from percentComplete if the user wants only some of the torrent's files.
        Range is [0..1]
        """
        return self.fields["percentDone"]

    @property
    def pieces(self) -> str:
        """
        A bitfield holding pieceCount flags which are set to 'true'
        if we have the piece matching that position.

        JSON doesn't allow raw binary data, so this is a base64-encoded string. (Source: tr_torrent)
        """
        return self.fields["pieces"]

    @property
    def piece_count(self) -> int:
        return self.fields["pieceCount"]

    @property
    def piece_size(self) -> int:
        return self.fields["pieceSize"]

    @property
    def priorities(self):
        # TODO
        return self.fields["priorities"]

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
        return self.fields["recheckProgress"]

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
    def seed_ratio_limit(self) -> float:
        """the default seed ratio for torrents to use"""
        return self.fields["seedRatioLimit"]

    @property
    def seed_ratio_mode(self) -> int:
        """which ratio to use. See tr_ratiolimit"""
        return self.fields["seedRatioMode"]

    @property
    def size_when_done(self) -> int:
        return self.fields["sizeWhenDone"]

    @property
    def start_date(self):
        # TODO
        return self.fields["startDate"]

    @property
    def status(self):
        # TODO
        return self.fields["status"]

    @property
    def trackers(self):
        # TODO
        return self.fields["trackers"]

    @property
    def tracker_list(self) -> List[str]:
        """list of str of announce URLs"""
        return [x for x in self.fields["trackerList"].splitlines() if x]

    @property
    def tracker_stats(self) -> List[TrackerStats]:
        return [TrackerStats(**x) for x in self.fields["trackerStats"]]

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
        return self.fields["uploadRatio"]

    @property
    def wanted(self) -> List:
        # TODO
        return self.fields["wanted"]

    @property
    def webseeds(self) -> List[str]:
        return self.fields["webseeds"]

    @property
    def webseeds_sending_to_us(self):
        """Number of webseeds that are sending data to us."""
        return self.fields["webseedsSendingToUs"]

    def _status(self) -> str:
        """Get the torrent status"""
        return get_status(self.fields["status"])

    @property
    def status(self) -> Status:
        """
        :rtype: Status

        Returns the torrent status. Is either one of 'check pending', 'checking',
        'downloading', 'download pending', 'seeding', 'seed pending' or 'stopped'.
        The first two is related to verification.

        Examples:

        .. code-block:: python

            torrent = Torrent()
            torrent.status.downloading
            torrent.status == 'downloading'

        """
        return Status(self._status())

    @property
    def progress(self) -> float:
        """
        download progress in percent.

        :rtype: float
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

        :rtype: float
        """
        return float(self.fields["uploadRatio"])

    @property
    def date_active(self) -> datetime:
        """the attribute ``activityDate`` as ``datetime.datetime`` in **UTC timezone**.

        .. note::

            raw ``activityDate`` value could be ``0`` for never activated torrent,
            therefore it can't always be converted to local timezone.

        """
        return datetime.fromtimestamp(self.fields["activityDate"], timezone.utc)

    @property
    def date_added(self) -> datetime:
        """raw field ``addedDate`` as ``datetime.datetime`` in **utc timezone**."""
        return datetime.fromtimestamp(self.fields["addedDate"], timezone.utc)

    @property
    def date_started(self) -> datetime:
        """raw field ``startDate`` as ``datetime.datetime`` in **utc timezone**."""
        return datetime.fromtimestamp(self.fields["startDate"], timezone.utc)

    @property
    def date_done(self) -> Optional[datetime]:
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
        return format_timedelta(self.eta)

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
    def priority(self) -> str:
        """
        Bandwidth priority as string.
        Can be one of 'low', 'normal', 'high'. This is a mutator.
        """

        return PRIORITY[self.fields["bandwidthPriority"]]

    # @property
    # def desired_available(self) -> int:
    #     """Bytes that are left to download and available"""
    #     return self.fields["desiredAvailable"]

    @property
    def seed_idle_mode(self) -> str:
        """
        Seed idle mode as string. Can be one of 'global', 'single' or 'unlimited'.

         * global, use session seed idle limit.
         * single, use torrent seed idle limit. See seed_idle_limit.
         * unlimited, no seed idle limit.
        """
        return IDLE_LIMIT[self.fields["seedIdleMode"]]

    @property
    def seed_ratio_limit(self) -> float:
        """
        Torrent seed ratio limit as float. Also see seed_ratio_mode.
        This is a mutator.

        :rtype: float
        """

        return float(self.fields["seedRatioLimit"])

    @property
    def seed_ratio_mode(self) -> str:
        """
        Seed ratio mode as string. Can be one of 'global', 'single' or 'unlimited'.

         * global, use session seed ratio limit.
         * single, use torrent seed ratio limit. See seed_ratio_limit.
         * unlimited, no seed ratio limit.

        This is a mutator.
        """
        return RATIO_LIMIT[self.fields["seedRatioMode"]]

    def __repr__(self) -> str:
        return f'<Torrent {self.id} "{self.name}">'

    def __str__(self) -> str:
        return f'Torrent "{self.name}"'
