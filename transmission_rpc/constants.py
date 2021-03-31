# Copyright (c) 2018-2020 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
import logging
from typing import Optional, NamedTuple

LOGGER = logging.getLogger("transmission-rpc")
LOGGER.setLevel(logging.ERROR)


def mirror_dict(source: dict) -> dict:
    """
    Creates a dictionary with all values as keys and all keys as values.
    """
    source.update({value: key for key, value in source.items()})
    return source


DEFAULT_TIMEOUT = 30.0

TR_PRI_LOW = -1
TR_PRI_NORMAL = 0
TR_PRI_HIGH = 1

PRIORITY = mirror_dict(
    {"low": TR_PRI_LOW, "normal": TR_PRI_NORMAL, "high": TR_PRI_HIGH}
)

TR_RATIOLIMIT_GLOBAL = 0  # follow the global settings
TR_RATIOLIMIT_SINGLE = 1  # override the global settings, seeding until a certain ratio
TR_RATIOLIMIT_UNLIMITED = 2  # override the global settings, seeding regardless of ratio

RATIO_LIMIT = mirror_dict(
    {
        "global": TR_RATIOLIMIT_GLOBAL,
        "single": TR_RATIOLIMIT_SINGLE,
        "unlimited": TR_RATIOLIMIT_UNLIMITED,
    }
)

TR_IDLELIMIT_GLOBAL = 0  # follow the global settings
TR_IDLELIMIT_SINGLE = (
    1  # override the global settings, seeding until a certain idle time
)
TR_IDLELIMIT_UNLIMITED = (
    2  # override the global settings, seeding regardless of activity
)

IDLE_LIMIT = mirror_dict(
    {
        "global": TR_RATIOLIMIT_GLOBAL,
        "single": TR_RATIOLIMIT_SINGLE,
        "unlimited": TR_RATIOLIMIT_UNLIMITED,
    }
)


class Args(NamedTuple):
    type: str
    added_version: int
    removed_version: Optional[int] = None
    previous_argument_name: Optional[str] = None
    next_argument_name: Optional[str] = None
    description: str = ""

    def __repr__(self) -> str:
        return (
            f"Args({self.type!r},"
            f" {self.added_version!r},"
            f" {self.removed_version!r},"
            f" {self.previous_argument_name!r},"
            f" {self.next_argument_name!r},"
            f" {self.description!r})"
        )

    def __str__(self) -> str:
        return f"Args<type={self.type}, added_version={self.added_version}, description={self.description!r})"


class BaseType:
    number = "number"
    string = "string"
    array = "array"
    boolean = "boolean"
    double = "double"
    object = "object"


# Arguments for torrent methods
TORRENT_ARGS = {
    "get": {
        "activityDate": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "Last time of upload or download activity.",
        ),
        "addedDate": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "The date when this torrent was first added.",
        ),
        "announceResponse": Args(
            BaseType.string, 1, 7, None, None, "The announce message from the tracker."
        ),
        "announceURL": Args(BaseType.string, 1, 7, None, None, "Current announce URL."),
        "comment": Args(BaseType.string, 1, None, None, None, "Torrent comment."),
        "corruptEver": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "Number of bytes of corrupt data downloaded.",
        ),
        "creator": Args(BaseType.string, 1, None, None, None, "Torrent creator."),
        "dateCreated": Args(
            BaseType.number, 1, None, None, None, "Torrent creation date."
        ),
        "desiredAvailable": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "Number of bytes available and left to be downloaded.",
        ),
        "doneDate": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "The date when the torrent finished downloading.",
        ),
        "downloadedEver": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "Number of bytes of good data downloaded.",
        ),
        "downloadLimit": Args(
            BaseType.number, 1, None, None, None, "Download limit in Kbps."
        ),
        "downloadLimitMode": Args(
            BaseType.number,
            1,
            5,
            None,
            None,
            "Download limit mode. 0 means global, 1 means single, 2 unlimited.",
        ),
        "error": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "Kind of error. 0 means OK, 1 means tracker warning, 2 means tracker error, 3 means local error.",
        ),
        "errorString": Args(BaseType.number, 1, None, None, None, "Error message."),
        "eta": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "Estimated number of seconds left when downloading or seeding. -1 means not available and -2 means unknown.",
        ),
        "files": Args(
            BaseType.array,
            1,
            None,
            None,
            None,
            "Array of file object containing key, bytesCompleted, length and name.",
        ),
        "hashString": Args(
            BaseType.string,
            1,
            None,
            None,
            None,
            "Hashstring unique for the torrent even between sessions.",
        ),
        "haveUnchecked": Args(
            BaseType.number, 1, None, None, None, "Number of bytes of partial pieces."
        ),
        "haveValid": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "Number of bytes of checksum verified data.",
        ),
        "id": Args(BaseType.number, 1, None, None, None, "Session unique torrent id."),
        "isPrivate": Args(
            BaseType.boolean, 1, None, None, None, "True if the torrent is private."
        ),
        "lastAnnounceTime": Args(
            BaseType.number, 1, 7, None, None, "The time of the last announcement."
        ),
        "lastScrapeTime": Args(
            BaseType.number, 1, 7, None, None, "The time af the last successful scrape."
        ),
        "leechers": Args(BaseType.number, 1, 7, None, None, "Number of leechers."),
        "leftUntilDone": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "Number of bytes left until the download is done.",
        ),
        "manualAnnounceTime": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "The time until you manually ask for more peers.",
        ),
        "maxConnectedPeers": Args(
            BaseType.number, 1, None, None, None, "Maximum of connected peers."
        ),
        "name": Args(BaseType.string, 1, None, None, None, "Torrent name."),
        "nextAnnounceTime": Args(
            BaseType.number, 1, 7, None, None, "Next announce time."
        ),
        "nextScrapeTime": Args(BaseType.number, 1, 7, None, None, "Next scrape time."),
        "peersConnected": Args(
            BaseType.number, 1, None, None, None, "Number of peers we are connected to."
        ),
        "peersFrom": Args(
            BaseType.object,
            1,
            None,
            None,
            None,
            "Object containing download peers counts for different peer types.",
        ),
        "peersGettingFromUs": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "Number of peers we are sending data to.",
        ),
        "peersKnown": Args(
            BaseType.number,
            1,
            13,
            None,
            None,
            "Number of peers that the tracker knows.",
        ),
        "peersSendingToUs": Args(
            BaseType.number, 1, None, None, None, "Number of peers sending to us"
        ),
        "pieceCount": Args(BaseType.number, 1, None, None, None, "Number of pieces."),
        "pieceSize": Args(
            BaseType.number, 1, None, None, None, "Number of bytes in a piece."
        ),
        "priorities": Args(
            BaseType.array, 1, None, None, None, "Array of file priorities."
        ),
        "rateDownload": Args(
            BaseType.number, 1, None, None, None, "Download rate in bps."
        ),
        "rateUpload": Args(BaseType.number, 1, None, None, None, "Upload rate in bps."),
        "recheckProgress": Args(
            BaseType.double, 1, None, None, None, "Progress of recheck. 0.0 to 1.0."
        ),
        "scrapeResponse": Args(
            BaseType.string, 1, 7, None, None, "Scrape response message."
        ),
        "scrapeURL": Args(BaseType.string, 1, 7, None, None, "Current scrape URL"),
        "seeders": Args(
            BaseType.number,
            1,
            7,
            None,
            None,
            "Number of seeders reported by the tracker.",
        ),
        "sizeWhenDone": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "Size of the torrent download in bytes.",
        ),
        "startDate": Args(
            BaseType.number,
            1,
            None,
            None,
            None,
            "The date when the torrent was last started.",
        ),
        "status": Args(
            BaseType.number, 1, None, None, None, "Current status, see source"
        ),
        "swarmSpeed": Args(
            BaseType.number, 1, 7, None, None, "Estimated speed in Kbps in the swarm."
        ),
        "timesCompleted": Args(
            BaseType.number,
            1,
            7,
            None,
            None,
            "Number of successful downloads reported by the tracker.",
        ),
        "trackers": Args(
            BaseType.array, 1, None, None, None, "Array of tracker objects."
        ),
        "totalSize": Args(
            BaseType.number, 1, None, None, None, "Total size of the torrent in bytes"
        ),
        "uploadedEver": Args(
            BaseType.number, 1, None, None, None, "Number of bytes uploaded, ever."
        ),
        "uploadLimit": Args(
            BaseType.number, 1, None, None, None, "Upload limit in Kbps"
        ),
        "uploadLimitMode": Args(
            BaseType.number,
            1,
            5,
            None,
            None,
            "Upload limit mode. 0 means global, 1 means single, 2 unlimited.",
        ),
        "uploadRatio": Args(BaseType.double, 1, None, None, None, "Seed ratio."),
        "wanted": Args(
            BaseType.array,
            1,
            None,
            None,
            None,
            "Array of booleans indicated wanted files.",
        ),
        "webseeds": Args(
            BaseType.array, 1, None, None, None, "Array of webseeds objects"
        ),
        "webseedsSendingToUs": Args(
            BaseType.number, 1, None, None, None, "Number of webseeds seeding to us."
        ),
        "peers": Args(BaseType.array, 2, None, None, None, "Array of peer objects."),
        "downloadDir": Args(
            BaseType.string,
            4,
            None,
            None,
            None,
            "The directory path where the torrent is downloaded to.",
        ),
        "downloaders": Args(
            BaseType.number, 4, 7, None, None, "Number of downloaders."
        ),
        "bandwidthPriority": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Bandwidth priority. Low (-1), Normal (0) or High (1).",
        ),
        "downloadLimited": Args(
            BaseType.boolean, 5, None, None, None, "Download limit is enabled"
        ),
        "fileStats": Args(
            BaseType.array,
            5,
            None,
            None,
            None,
            "Away of file statistics containing bytesCompleted, wanted and priority.",
        ),
        "honorsSessionLimits": Args(
            BaseType.boolean,
            5,
            None,
            None,
            None,
            "True if session upload limits are honored",
        ),
        "peer-limit": Args(
            BaseType.number, 5, None, None, None, "Maximum number of peers."
        ),
        "percentDone": Args(
            BaseType.double,
            5,
            None,
            None,
            None,
            "Download progress of selected files. 0.0 to 1.0.",
        ),
        "pieces": Args(
            BaseType.string,
            5,
            None,
            None,
            None,
            "String with base64 encoded bitfield indicating finished pieces.",
        ),
        "seedRatioLimit": Args(
            BaseType.double, 5, None, None, None, "Seed ratio limit."
        ),
        "seedRatioMode": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Use global (0), torrent (1), or unlimited (2) limit.",
        ),
        "torrentFile": Args(
            BaseType.string, 5, None, None, None, "Path to .torrent file."
        ),
        "uploadLimited": Args(
            BaseType.boolean, 5, None, None, None, "Upload limit enabled."
        ),
        "magnetLink": Args(
            BaseType.string, 7, None, None, None, "The magnet link for this torrent."
        ),
        "metadataPercentComplete": Args(
            BaseType.number,
            7,
            None,
            None,
            None,
            "Download progress of metadata. 0.0 to 1.0.",
        ),
        "trackerStats": Args(
            BaseType.object,
            7,
            None,
            None,
            None,
            "Array of object containing tracker statistics.",
        ),
        "isFinished": Args(
            BaseType.boolean,
            9,
            None,
            None,
            None,
            "True if the torrent is finished. Downloaded and seeded.",
        ),
        "seedIdleLimit": Args(
            BaseType.number, 10, None, None, None, "Idle limit in minutes."
        ),
        "seedIdleMode": Args(
            BaseType.number,
            10,
            None,
            None,
            None,
            "Use global (0), torrent (1), or unlimited (2) limit.",
        ),
        "isStalled": Args(
            BaseType.boolean,
            14,
            None,
            None,
            None,
            "True if the torrent has stalled (been idle for a long time).",
        ),
        "queuePosition": Args(
            BaseType.number, 14, None, None, None, "The queue position."
        ),
        "etaIdle": Args(
            BaseType.number,
            15,
            description=(
                "Estimated number of seconds left until the idle time limit is reached."
                " -1 means not available and -2 means unknown."
            ),
        ),
        "secondsDownloading": Args(BaseType.number, 15, None, None, None, ""),
        "secondsSeeding": Args(BaseType.number, 15, None, None, None, ""),
        "labels": Args(BaseType.array, 16, None, None, None, "array of string labels"),
        "editDate": Args(BaseType.number, 16),
        "file-count": Args(BaseType.number, 17),
        "primary-mime-type": Args(BaseType.string, 17),
    },
    "set": {
        "files-wanted": Args(
            BaseType.array,
            1,
            None,
            None,
            None,
            "A list of file id's that should be downloaded.",
        ),
        "files-unwanted": Args(
            BaseType.array,
            1,
            None,
            None,
            None,
            "A list of file id's that shouldn't be downloaded.",
        ),
        "location": Args(
            BaseType.array, 1, None, None, None, "Local download location."
        ),
        "peer-limit": Args(
            BaseType.number, 1, None, None, None, "The peer limit for the torrents."
        ),
        "priority-high": Args(
            BaseType.array,
            1,
            None,
            None,
            None,
            "A list of file id's that should have high priority.",
        ),
        "priority-low": Args(
            BaseType.array,
            1,
            None,
            None,
            None,
            "A list of file id's that should have normal priority.",
        ),
        "priority-normal": Args(
            BaseType.array,
            1,
            None,
            None,
            None,
            "A list of file id's that should have low priority.",
        ),
        "speed-limit-down": Args(
            BaseType.number,
            1,
            5,
            None,
            "downloadLimit",
            "Set the speed limit for download in Kib/s.",
        ),
        "speed-limit-down-enabled": Args(
            BaseType.boolean,
            1,
            5,
            None,
            "downloadLimited",
            "Enable download speed limiter.",
        ),
        "speed-limit-up": Args(
            BaseType.number,
            1,
            5,
            None,
            "uploadLimit",
            "Set the speed limit for upload in Kib/s.",
        ),
        "speed-limit-up-enabled": Args(
            BaseType.boolean,
            1,
            5,
            None,
            "uploadLimited",
            "Enable upload speed limiter.",
        ),
        "bandwidthPriority": Args(
            BaseType.number, 5, None, None, None, "Priority for this transfer."
        ),
        "downloadLimit": Args(
            BaseType.number,
            5,
            None,
            "speed-limit-down",
            None,
            "Set the speed limit for download in Kib/s.",
        ),
        "downloadLimited": Args(
            BaseType.boolean,
            5,
            None,
            "speed-limit-down-enabled",
            None,
            "Enable download speed limiter.",
        ),
        "honorsSessionLimits": Args(
            BaseType.boolean,
            5,
            None,
            None,
            None,
            "Enables or disables the transfer to honour the upload limit set in the session.",
        ),
        "seedRatioLimit": Args(BaseType.double, 5, None, None, None, "Seeding ratio."),
        "seedRatioMode": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Which ratio to use. 0 = Use session limit, 1 = Use transfer limit, 2 = Disable limit.",
        ),
        "uploadLimit": Args(
            BaseType.number,
            5,
            None,
            "speed-limit-up",
            None,
            "Set the speed limit for upload in Kib/s.",
        ),
        "uploadLimited": Args(
            BaseType.boolean,
            5,
            None,
            "speed-limit-up-enabled",
            None,
            "Enable upload speed limiter.",
        ),
        "seedIdleLimit": Args(
            BaseType.number, 10, None, None, None, "Seed inactivity limit in minutes."
        ),
        "seedIdleMode": Args(
            BaseType.number,
            10,
            None,
            None,
            None,
            "Seed inactivity mode. 0 = Use session limit, 1 = Use transfer limit, 2 = Disable limit.",
        ),
        "trackerAdd": Args(
            BaseType.array,
            10,
            None,
            None,
            None,
            "Array of string with announce URLs to add.",
        ),
        "trackerRemove": Args(
            BaseType.array, 10, None, None, None, "Array of ids of trackers to remove."
        ),
        "trackerReplace": Args(
            BaseType.array,
            10,
            None,
            None,
            None,
            "Array of (id, url) tuples where the announce URL should be replaced.",
        ),
        "queuePosition": Args(
            BaseType.number,
            14,
            None,
            None,
            None,
            "Position of this transfer in its queue.",
        ),
        "labels": Args(BaseType.array, 16, None, None, None, "array of string labels"),
    },
    "add": {
        "download-dir": Args(
            BaseType.string,
            1,
            None,
            None,
            None,
            "The directory where the downloaded contents will be saved in.",
        ),
        "filename": Args(
            BaseType.string,
            1,
            None,
            None,
            None,
            "A file path or URL to a torrent file or a magnet link.",
        ),
        "files-wanted": Args(
            BaseType.array,
            1,
            None,
            None,
            None,
            "A list of file id's that should be downloaded.",
        ),
        "files-unwanted": Args(
            BaseType.array,
            1,
            None,
            None,
            None,
            "A list of file id's that shouldn't be downloaded.",
        ),
        "metainfo": Args(
            BaseType.string,
            1,
            None,
            None,
            None,
            "The content of a torrent file, base64 encoded.",
        ),
        "paused": Args(
            BaseType.boolean,
            1,
            None,
            None,
            None,
            "If True, does not start the transfer when added.",
        ),
        "peer-limit": Args(
            BaseType.number, 1, None, None, None, "Maximum number of peers allowed."
        ),
        "priority-high": Args(
            BaseType.array,
            1,
            None,
            None,
            None,
            "A list of file id's that should have high priority.",
        ),
        "priority-low": Args(
            BaseType.array,
            1,
            None,
            None,
            None,
            "A list of file id's that should have low priority.",
        ),
        "priority-normal": Args(
            BaseType.array,
            1,
            None,
            None,
            None,
            "A list of file id's that should have normal priority.",
        ),
        "bandwidthPriority": Args(
            BaseType.number, 8, None, None, None, "Priority for this transfer."
        ),
        "cookies": Args(
            BaseType.string, 13, None, None, None, "One or more HTTP cookie(s)."
        ),
    },
}


# Arguments for session methods
SESSION_ARGS = {
    "get": {
        "download-dir": Args(
            BaseType.string, 1, None, None, None, "The download directory."
        ),
        "encryption": Args(
            BaseType.string,
            1,
            None,
            None,
            None,
            "Encryption mode, one of ``required``, ``preferred`` or ``tolerated``.",
        ),
        "peer-limit": Args(
            BaseType.number, 1, 5, None, "peer-limit-global", "Maximum number of peers."
        ),
        "pex-allowed": Args(
            BaseType.boolean, 1, 5, None, "pex-enabled", "True if PEX is allowed."
        ),
        "port": Args(BaseType.number, 1, 5, None, "peer-port", "Peer port."),
        "port-forwarding-enabled": Args(
            BaseType.boolean, 1, None, None, None, "True if port forwarding is enabled."
        ),
        "speed-limit-down": Args(
            BaseType.number, 1, None, None, None, "Download speed limit (in Kib/s)."
        ),
        "speed-limit-down-enabled": Args(
            BaseType.boolean,
            1,
            None,
            None,
            None,
            "True if the download speed is limited.",
        ),
        "speed-limit-up": Args(
            BaseType.number, 1, None, None, None, "Upload speed limit (in Kib/s)."
        ),
        "speed-limit-up-enabled": Args(
            BaseType.boolean,
            1,
            None,
            None,
            None,
            "True if the upload speed is limited.",
        ),
        "version": Args(BaseType.string, 3, None, None, None, "Transmission version."),
        "rpc-version": Args(
            BaseType.number, 4, None, None, None, "Transmission RPC API Version."
        ),
        "rpc-version-minimum": Args(
            BaseType.number, 4, None, None, None, "Minimum accepted RPC API Version."
        ),
        "alt-speed-down": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Alternate session download speed limit (in Kib/s).",
        ),
        "alt-speed-enabled": Args(
            BaseType.boolean,
            5,
            None,
            None,
            None,
            "True if alternate global download speed limiter is enabled.",
        ),
        "alt-speed-time-begin": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Time when alternate speeds should be enabled. Minutes after midnight.",
        ),
        "alt-speed-time-enabled": Args(
            BaseType.boolean,
            5,
            None,
            None,
            None,
            "True if alternate speeds scheduling is enabled.",
        ),
        "alt-speed-time-end": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Time when alternate speeds should be disabled. Minutes after midnight.",
        ),
        "alt-speed-time-day": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Days alternate speeds scheduling is enabled.",
        ),
        "alt-speed-up": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Alternate session upload speed limit (in Kib/s)",
        ),
        "blocklist-enabled": Args(
            BaseType.boolean, 5, None, None, None, "True when blocklist is enabled."
        ),
        "blocklist-size": Args(
            BaseType.number, 5, None, None, None, "Number of rules in the blocklist"
        ),
        "peer-limit-global": Args(
            BaseType.number, 5, None, "peer-limit", None, "Maximum number of peers."
        ),
        "peer-limit-per-torrent": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Maximum number of peers per transfer.",
        ),
        "pex-enabled": Args(
            BaseType.boolean, 5, None, "pex-allowed", None, "True if PEX is enabled."
        ),
        "peer-port": Args(BaseType.number, 5, None, "port", None, "Peer port."),
        "peer-port-random-on-start": Args(
            BaseType.boolean,
            5,
            None,
            None,
            None,
            "Enables randomized peer port on start of Transmission.",
        ),
        "seedRatioLimit": Args(
            BaseType.double,
            5,
            None,
            None,
            None,
            "Seed ratio limit. 1.0 means 1:1 download and upload ratio.",
        ),
        "seedRatioLimited": Args(
            BaseType.boolean,
            5,
            None,
            None,
            None,
            "True if seed ration limit is enabled.",
        ),
        "dht-enabled": Args(
            BaseType.boolean, 6, None, None, None, "True if DHT enabled."
        ),
        "incomplete-dir": Args(
            BaseType.string,
            7,
            None,
            None,
            None,
            "The path to the directory for incomplete torrent transfer data.",
        ),
        "incomplete-dir-enabled": Args(
            BaseType.boolean,
            7,
            None,
            None,
            None,
            "True if the incomplete dir is enabled.",
        ),
        "config-dir": Args(
            BaseType.string,
            8,
            None,
            None,
            None,
            "location of transmissions configuration directory",
        ),
        "rename-partial-files": Args(
            BaseType.boolean,
            8,
            None,
            None,
            None,
            'True if ".part" is appended to incomplete files',
        ),
        "lpd-enabled": Args(
            BaseType.boolean,
            9,
            None,
            None,
            None,
            "True if local peer discovery is enabled.",
        ),
        "script-torrent-done-enabled": Args(
            BaseType.boolean, 9, None, None, None, "True if the done script is enabled."
        ),
        "script-torrent-done-filename": Args(
            BaseType.string,
            9,
            None,
            None,
            None,
            "Filename of the script to run when the transfer is done.",
        ),
        "start-added-torrents": Args(
            BaseType.boolean,
            9,
            None,
            None,
            None,
            "When true uploaded torrents will start right away.",
        ),
        "trash-original-torrent-files": Args(
            BaseType.boolean,
            9,
            None,
            None,
            None,
            "When true added .torrent files will be deleted.",
        ),
        "cache-size-mb": Args(
            BaseType.number,
            10,
            None,
            None,
            None,
            "The maximum size of the disk cache in MB",
        ),
        "idle-seeding-limit": Args(
            BaseType.number, 10, None, None, None, "Seed inactivity limit in minutes."
        ),
        "idle-seeding-limit-enabled": Args(
            BaseType.boolean,
            10,
            None,
            None,
            None,
            "True if the seed activity limit is enabled.",
        ),
        "units": Args(
            BaseType.object,
            10,
            None,
            None,
            None,
            "An object containing units for size and speed.",
        ),
        "blocklist-url": Args(
            BaseType.string,
            11,
            None,
            None,
            None,
            "Location of the block list. Updated with blocklist-update.",
        ),
        "download-dir-free-space": Args(
            BaseType.number,
            12,
            None,
            None,
            None,
            "Free space in the download directory, in bytes",
        ),
        "utp-enabled": Args(
            BaseType.boolean,
            13,
            None,
            None,
            None,
            "True if Micro Transport Protocol (UTP) is enabled.",
        ),
        "download-queue-size": Args(
            BaseType.number,
            14,
            None,
            None,
            None,
            "Number of slots in the download queue.",
        ),
        "download-queue-enabled": Args(
            BaseType.boolean,
            14,
            None,
            None,
            None,
            "True if the download queue is enabled.",
        ),
        "queue-stalled-minutes": Args(
            BaseType.number,
            14,
            None,
            None,
            None,
            "Number of minutes of idle that marks a transfer as stalled.",
        ),
        "queue-stalled-enabled": Args(
            BaseType.boolean,
            14,
            None,
            None,
            None,
            "True if stalled tracking of transfers is enabled.",
        ),
        "seed-queue-size": Args(
            BaseType.number,
            14,
            None,
            None,
            None,
            "Number of slots in the upload queue.",
        ),
        "seed-queue-enabled": Args(
            BaseType.boolean, 14, None, None, None, "True if upload queue is enabled."
        ),
        "fields": Args(BaseType.array, 16, None, None, None, "array of keys"),
        "session-id": Args(BaseType.string, 16, None, None, None, "session-id"),
    },
    "set": {
        "download-dir": Args(
            BaseType.string, 1, None, None, None, "Set the session download directory."
        ),
        "encryption": Args(
            BaseType.string,
            1,
            None,
            None,
            None,
            "Set the session encryption mode, one of ``required``, ``preferred`` or ``tolerated``.",
        ),
        "peer-limit": Args(
            BaseType.number, 1, 5, None, "peer-limit-global", "Maximum number of peers."
        ),
        "pex-allowed": Args(
            BaseType.boolean,
            1,
            5,
            None,
            "pex-enabled",
            "Allowing PEX in public torrents.",
        ),
        "port": Args(BaseType.number, 1, 5, None, "peer-port", "Peer port."),
        "port-forwarding-enabled": Args(
            BaseType.boolean, 1, None, None, None, "Enables port forwarding."
        ),
        "speed-limit-down": Args(
            BaseType.number, 1, None, None, None, "Download speed limit (in Kib/s)."
        ),
        "speed-limit-down-enabled": Args(
            BaseType.boolean, 1, None, None, None, "Enables download speed limiting."
        ),
        "speed-limit-up": Args(
            BaseType.number, 1, None, None, None, "Upload speed limit (in Kib/s)."
        ),
        "speed-limit-up-enabled": Args(
            BaseType.boolean, 1, None, None, None, "Enables upload speed limiting."
        ),
        "alt-speed-down": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Alternate session download speed limit (in Kib/s).",
        ),
        "alt-speed-enabled": Args(
            BaseType.boolean,
            5,
            None,
            None,
            None,
            "Enables alternate global download speed limiter.",
        ),
        "alt-speed-time-begin": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Time when alternate speeds should be enabled. Minutes after midnight.",
        ),
        "alt-speed-time-enabled": Args(
            BaseType.boolean,
            5,
            None,
            None,
            None,
            "Enables alternate speeds scheduling.",
        ),
        "alt-speed-time-end": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Time when alternate speeds should be disabled. Minutes after midnight.",
        ),
        "alt-speed-time-day": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Enables alternate speeds scheduling these days.",
        ),
        "alt-speed-up": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Alternate session upload speed limit (in Kib/s).",
        ),
        "blocklist-enabled": Args(
            BaseType.boolean, 5, None, None, None, "Enables the block list"
        ),
        "peer-limit-global": Args(
            BaseType.number, 5, None, "peer-limit", None, "Maximum number of peers."
        ),
        "peer-limit-per-torrent": Args(
            BaseType.number,
            5,
            None,
            None,
            None,
            "Maximum number of peers per transfer.",
        ),
        "pex-enabled": Args(
            BaseType.boolean,
            5,
            None,
            "pex-allowed",
            None,
            "Allowing PEX in public torrents.",
        ),
        "peer-port": Args(BaseType.number, 5, None, "port", None, "Peer port."),
        "peer-port-random-on-start": Args(
            BaseType.boolean,
            5,
            None,
            None,
            None,
            "Enables randomized peer port on start of Transmission.",
        ),
        "seedRatioLimit": Args(
            BaseType.double,
            5,
            None,
            None,
            None,
            "Seed ratio limit. 1.0 means 1:1 download and upload ratio.",
        ),
        "seedRatioLimited": Args(
            BaseType.boolean, 5, None, None, None, "Enables seed ration limit."
        ),
        "dht-enabled": Args(BaseType.boolean, 6, None, None, None, "Enables DHT."),
        "incomplete-dir": Args(
            BaseType.string,
            7,
            None,
            None,
            None,
            "The path to the directory of incomplete transfer data.",
        ),
        "incomplete-dir-enabled": Args(
            BaseType.boolean,
            7,
            None,
            None,
            None,
            "Enables the incomplete transfer data directory. Otherwise data for incomplete transfers are stored in the download target.",
        ),
        "rename-partial-files": Args(
            BaseType.boolean, 8, None, None, None, 'Appends ".part" to incomplete files'
        ),
        "lpd-enabled": Args(
            BaseType.boolean,
            9,
            None,
            None,
            None,
            "Enables local peer discovery for public torrents.",
        ),
        "script-torrent-done-enabled": Args(
            BaseType.boolean,
            9,
            None,
            None,
            None,
            'Whether or not to call the "done" script.',
        ),
        "script-torrent-done-filename": Args(
            BaseType.string,
            9,
            None,
            None,
            None,
            "Filename of the script to run when the transfer is done.",
        ),
        "start-added-torrents": Args(
            BaseType.boolean,
            9,
            None,
            None,
            None,
            "Added torrents will be started right away.",
        ),
        "trash-original-torrent-files": Args(
            BaseType.boolean,
            9,
            None,
            None,
            None,
            "The .torrent file of added torrents will be deleted.",
        ),
        "cache-size-mb": Args(
            BaseType.number,
            10,
            None,
            None,
            None,
            "The maximum size of the disk cache in MB",
        ),
        "idle-seeding-limit": Args(
            BaseType.number,
            10,
            None,
            None,
            None,
            "The default seed inactivity limit in minutes.",
        ),
        "idle-seeding-limit-enabled": Args(
            BaseType.boolean,
            10,
            None,
            None,
            None,
            "Enables the default seed inactivity limit",
        ),
        "blocklist-url": Args(
            BaseType.string,
            11,
            None,
            None,
            None,
            "Location of the block list. Updated with blocklist-update.",
        ),
        "utp-enabled": Args(
            BaseType.boolean,
            13,
            None,
            None,
            None,
            "Enables Micro Transport Protocol (UTP).",
        ),
        "download-queue-size": Args(
            BaseType.number,
            14,
            None,
            None,
            None,
            "Number of slots in the download queue.",
        ),
        "download-queue-enabled": Args(
            BaseType.boolean, 14, None, None, None, "Enables download queue."
        ),
        "queue-stalled-minutes": Args(
            BaseType.number,
            14,
            None,
            None,
            None,
            "Number of minutes of idle that marks a transfer as stalled.",
        ),
        "queue-stalled-enabled": Args(
            BaseType.boolean,
            14,
            None,
            None,
            None,
            "Enable tracking of stalled transfers.",
        ),
        "seed-queue-size": Args(
            BaseType.number,
            14,
            None,
            None,
            None,
            "Number of slots in the upload queue.",
        ),
        "seed-queue-enabled": Args(
            BaseType.boolean, 14, None, None, None, "Enables upload queue."
        ),
    },
}
