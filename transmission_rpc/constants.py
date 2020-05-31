# Copyright (c) 2018-2020 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.

import logging
from typing import Optional, NamedTuple

LOGGER = logging.getLogger('transmission-rpc')
LOGGER.setLevel(logging.ERROR)


def mirror_dict(source):
    """
    Creates a dictionary with all values as keys and all keys as values.
    """
    source.update({value: key for key, value in source.items()})
    return source


DEFAULT_TIMEOUT = 30.0

TR_PRI_LOW = -1
TR_PRI_NORMAL = 0
TR_PRI_HIGH = 1

PRIORITY = mirror_dict({'low': TR_PRI_LOW, 'normal': TR_PRI_NORMAL, 'high': TR_PRI_HIGH})

TR_RATIOLIMIT_GLOBAL = 0  # follow the global settings
TR_RATIOLIMIT_SINGLE = 1  # override the global settings, seeding until a certain ratio
TR_RATIOLIMIT_UNLIMITED = 2  # override the global settings, seeding regardless of ratio

RATIO_LIMIT = mirror_dict({
    'global': TR_RATIOLIMIT_GLOBAL, 'single': TR_RATIOLIMIT_SINGLE,
    'unlimited': TR_RATIOLIMIT_UNLIMITED
})

TR_IDLELIMIT_GLOBAL = 0  # follow the global settings
TR_IDLELIMIT_SINGLE = 1  # override the global settings, seeding until a certain idle time
TR_IDLELIMIT_UNLIMITED = 2  # override the global settings, seeding regardless of activity

IDLE_LIMIT = mirror_dict({
    'global': TR_RATIOLIMIT_GLOBAL, 'single': TR_RATIOLIMIT_SINGLE,
    'unlimited': TR_RATIOLIMIT_UNLIMITED
})


class Args(NamedTuple):
    type: str
    added_version: int
    removed_version: Optional[int]
    previous_argument_name: Optional[str]
    next_argument_name: Optional[str]
    description: str


# Arguments for torrent methods
TORRENT_ARGS = {
    'get': {
        'activityDate': Args(
            'number', 1, None, None, None, 'Last time of upload or download activity.'
        ),
        'addedDate': Args(
            'number', 1, None, None, None, 'The date when this torrent was first added.'
        ),
        'announceResponse': Args(
            'string', 1, 7, None, None, 'The announce message from the tracker.'
        ),
        'announceURL': Args('string', 1, 7, None, None, 'Current announce URL.'),
        'bandwidthPriority': Args(
            'number', 5, None, None, None, 'Bandwidth priority. Low (-1), Normal (0) or High (1).'
        ),
        'comment': Args('string', 1, None, None, None, 'Torrent comment.'),
        'corruptEver': Args(
            'number', 1, None, None, None, 'Number of bytes of corrupt data downloaded.'
        ),
        'creator': Args('string', 1, None, None, None, 'Torrent creator.'),
        'dateCreated': Args('number', 1, None, None, None, 'Torrent creation date.'),
        'desiredAvailable': Args(
            'number', 1, None, None, None, 'Number of bytes available and left to be downloaded.'
        ),
        'doneDate': Args(
            'number', 1, None, None, None, 'The date when the torrent finished downloading.'
        ),
        'downloadDir': Args(
            'string', 4, None, None, None, 'The directory path where the torrent is downloaded to.'
        ),
        'downloadedEver': Args(
            'number', 1, None, None, None, 'Number of bytes of good data downloaded.'
        ),
        'downloaders': Args('number', 4, 7, None, None, 'Number of downloaders.'),
        'downloadLimit': Args('number', 1, None, None, None, 'Download limit in Kbps.'),
        'downloadLimited': Args('boolean', 5, None, None, None, 'Download limit is enabled'),
        'downloadLimitMode': Args(
            'number', 1, 5, None, None,
            'Download limit mode. 0 means global, 1 means single, 2 unlimited.'
        ),
        'error': Args(
            'number', 1, None, None, None,
            'Kind of error. 0 means OK, 1 means tracker warning, 2 means tracker error, 3 means local error.'
        ),
        'errorString': Args('number', 1, None, None, None, 'Error message.'),
        'eta': Args(
            'number', 1, None, None, None,
            'Estimated number of seconds left when downloading or seeding. -1 means not available and -2 means unknown.'
        ),
        'etaIdle': Args(
            'number', 15, None, None, None,
            'Estimated number of seconds left until the idle time limit is reached. -1 means not available and -2 means unknown.'
        ),
        'files': Args(
            'array', 1, None, None, None,
            'Array of file object containing key, bytesCompleted, length and name.'
        ),
        'fileStats': Args(
            'array', 5, None, None, None,
            'Away of file statistics containing bytesCompleted, wanted and priority.'
        ),
        'hashString': Args(
            'string', 1, None, None, None,
            'Hashstring unique for the torrent even between sessions.'
        ),
        'haveUnchecked': Args('number', 1, None, None, None, 'Number of bytes of partial pieces.'),
        'haveValid': Args(
            'number', 1, None, None, None, 'Number of bytes of checksum verified data.'
        ),
        'honorsSessionLimits': Args(
            'boolean', 5, None, None, None, 'True if session upload limits are honored'
        ),
        'id': Args('number', 1, None, None, None, 'Session unique torrent id.'),
        'isFinished': Args(
            'boolean', 9, None, None, None,
            'True if the torrent is finished. Downloaded and seeded.'
        ),
        'isPrivate': Args('boolean', 1, None, None, None, 'True if the torrent is private.'),
        'isStalled': Args(
            'boolean', 14, None, None, None,
            'True if the torrent has stalled (been idle for a long time).'
        ),
        'lastAnnounceTime': Args('number', 1, 7, None, None, 'The time of the last announcement.'),
        'lastScrapeTime': Args(
            'number', 1, 7, None, None, 'The time af the last successful scrape.'
        ),
        'leechers': Args('number', 1, 7, None, None, 'Number of leechers.'),
        'leftUntilDone': Args(
            'number', 1, None, None, None, 'Number of bytes left until the download is done.'
        ),
        'magnetLink': Args('string', 7, None, None, None, 'The magnet link for this torrent.'),
        'manualAnnounceTime': Args(
            'number', 1, None, None, None, 'The time until you manually ask for more peers.'
        ),
        'maxConnectedPeers': Args('number', 1, None, None, None, 'Maximum of connected peers.'),
        'metadataPercentComplete': Args(
            'number', 7, None, None, None, 'Download progress of metadata. 0.0 to 1.0.'
        ),
        'name': Args('string', 1, None, None, None, 'Torrent name.'),
        'nextAnnounceTime': Args('number', 1, 7, None, None, 'Next announce time.'),
        'nextScrapeTime': Args('number', 1, 7, None, None, 'Next scrape time.'),
        'peer-limit': Args('number', 5, None, None, None, 'Maximum number of peers.'),
        'peers': Args('array', 2, None, None, None, 'Array of peer objects.'),
        'peersConnected': Args(
            'number', 1, None, None, None, 'Number of peers we are connected to.'
        ),
        'peersFrom': Args(
            'object', 1, None, None, None,
            'Object containing download peers counts for different peer types.'
        ),
        'peersGettingFromUs': Args(
            'number', 1, None, None, None, 'Number of peers we are sending data to.'
        ),
        'peersKnown': Args('number', 1, 13, None, None, 'Number of peers that the tracker knows.'),
        'peersSendingToUs': Args('number', 1, None, None, None, 'Number of peers sending to us'),
        'percentDone': Args(
            'double', 5, None, None, None, 'Download progress of selected files. 0.0 to 1.0.'
        ),
        'pieces': Args(
            'string', 5, None, None, None,
            'String with base64 encoded bitfield indicating finished pieces.'
        ),
        'pieceCount': Args('number', 1, None, None, None, 'Number of pieces.'),
        'pieceSize': Args('number', 1, None, None, None, 'Number of bytes in a piece.'),
        'priorities': Args('array', 1, None, None, None, 'Array of file priorities.'),
        'queuePosition': Args('number', 14, None, None, None, 'The queue position.'),
        'rateDownload': Args('number', 1, None, None, None, 'Download rate in bps.'),
        'rateUpload': Args('number', 1, None, None, None, 'Upload rate in bps.'),
        'recheckProgress': Args('double', 1, None, None, None, 'Progress of recheck. 0.0 to 1.0.'),
        'secondsDownloading': Args('number', 15, None, None, None, ''),
        'secondsSeeding': Args('number', 15, None, None, None, ''),
        'scrapeResponse': Args('string', 1, 7, None, None, 'Scrape response message.'),
        'scrapeURL': Args('string', 1, 7, None, None, 'Current scrape URL'),
        'seeders': Args('number', 1, 7, None, None, 'Number of seeders reported by the tracker.'),
        'seedIdleLimit': Args('number', 10, None, None, None, 'Idle limit in minutes.'),
        'seedIdleMode': Args(
            'number', 10, None, None, None, 'Use global (0), torrent (1), or unlimited (2) limit.'
        ),
        'seedRatioLimit': Args('double', 5, None, None, None, 'Seed ratio limit.'),
        'seedRatioMode': Args(
            'number', 5, None, None, None, 'Use global (0), torrent (1), or unlimited (2) limit.'
        ),
        'sizeWhenDone': Args(
            'number', 1, None, None, None, 'Size of the torrent download in bytes.'
        ),
        'startDate': Args(
            'number', 1, None, None, None, 'The date when the torrent was last started.'
        ),
        'status': Args('number', 1, None, None, None, 'Current status, see source'),
        'swarmSpeed': Args('number', 1, 7, None, None, 'Estimated speed in Kbps in the swarm.'),
        'timesCompleted': Args(
            'number', 1, 7, None, None, 'Number of successful downloads reported by the tracker.'
        ),
        'trackers': Args('array', 1, None, None, None, 'Array of tracker objects.'),
        'trackerStats': Args(
            'object', 7, None, None, None, 'Array of object containing tracker statistics.'
        ),
        'totalSize': Args('number', 1, None, None, None, 'Total size of the torrent in bytes'),
        'torrentFile': Args('string', 5, None, None, None, 'Path to .torrent file.'),
        'uploadedEver': Args('number', 1, None, None, None, 'Number of bytes uploaded, ever.'),
        'uploadLimit': Args('number', 1, None, None, None, 'Upload limit in Kbps'),
        'uploadLimitMode': Args(
            'number', 1, 5, None, None,
            'Upload limit mode. 0 means global, 1 means single, 2 unlimited.'
        ),
        'uploadLimited': Args('boolean', 5, None, None, None, 'Upload limit enabled.'),
        'uploadRatio': Args('double', 1, None, None, None, 'Seed ratio.'),
        'wanted': Args('array', 1, None, None, None, 'Array of booleans indicated wanted files.'),
        'webseeds': Args('array', 1, None, None, None, 'Array of webseeds objects'),
        'webseedsSendingToUs': Args(
            'number', 1, None, None, None, 'Number of webseeds seeding to us.'
        ),
    }, 'set': {
        'bandwidthPriority': Args('number', 5, None, None, None, 'Priority for this transfer.'),
        'downloadLimit': Args(
            'number', 5, None, 'speed-limit-down', None,
            'Set the speed limit for download in Kib/s.'
        ),
        'downloadLimited': Args(
            'boolean', 5, None, 'speed-limit-down-enabled', None, 'Enable download speed limiter.'
        ),
        'files-wanted': Args(
            'array', 1, None, None, None, "A list of file id's that should be downloaded."
        ),
        'files-unwanted': Args(
            'array', 1, None, None, None, "A list of file id's that shouldn't be downloaded."
        ),
        'honorsSessionLimits': Args(
            'boolean', 5, None, None, None,
            'Enables or disables the transfer to honour the upload limit set in the session.'
        ),
        'location': Args('array', 1, None, None, None, 'Local download location.'),
        'peer-limit': Args('number', 1, None, None, None, 'The peer limit for the torrents.'),
        'priority-high': Args(
            'array', 1, None, None, None, "A list of file id's that should have high priority."
        ),
        'priority-low': Args(
            'array', 1, None, None, None, "A list of file id's that should have normal priority."
        ),
        'priority-normal': Args(
            'array', 1, None, None, None, "A list of file id's that should have low priority."
        ),
        'queuePosition': Args(
            'number', 14, None, None, None, 'Position of this transfer in its queue.'
        ),
        'seedIdleLimit': Args('number', 10, None, None, None, 'Seed inactivity limit in minutes.'),
        'seedIdleMode': Args(
            'number', 10, None, None, None,
            'Seed inactivity mode. 0 = Use session limit, 1 = Use transfer limit, 2 = Disable limit.'
        ),
        'seedRatioLimit': Args('double', 5, None, None, None, 'Seeding ratio.'),
        'seedRatioMode': Args(
            'number', 5, None, None, None,
            'Which ratio to use. 0 = Use session limit, 1 = Use transfer limit, 2 = Disable limit.'
        ),
        'speed-limit-down': Args(
            'number', 1, 5, None, 'downloadLimit', 'Set the speed limit for download in Kib/s.'
        ),
        'speed-limit-down-enabled': Args(
            'boolean', 1, 5, None, 'downloadLimited', 'Enable download speed limiter.'
        ),
        'speed-limit-up': Args(
            'number', 1, 5, None, 'uploadLimit', 'Set the speed limit for upload in Kib/s.'
        ),
        'speed-limit-up-enabled': Args(
            'boolean', 1, 5, None, 'uploadLimited', 'Enable upload speed limiter.'
        ),
        'trackerAdd': Args(
            'array', 10, None, None, None, 'Array of string with announce URLs to add.'
        ),
        'trackerRemove': Args('array', 10, None, None, None, 'Array of ids of trackers to remove.'),
        'trackerReplace': Args(
            'array', 10, None, None, None,
            'Array of (id, url) tuples where the announce URL should be replaced.'
        ),
        'uploadLimit': Args(
            'number', 5, None, 'speed-limit-up', None, 'Set the speed limit for upload in Kib/s.'
        ),
        'uploadLimited': Args(
            'boolean', 5, None, 'speed-limit-up-enabled', None, 'Enable upload speed limiter.'
        ),
    }, 'add': {
        'bandwidthPriority': Args('number', 8, None, None, None, 'Priority for this transfer.'),
        'download-dir': Args(
            'string', 1, None, None, None,
            'The directory where the downloaded contents will be saved in.'
        ),
        'cookies': Args('string', 13, None, None, None, 'One or more HTTP cookie(s).'),
        'filename': Args(
            'string', 1, None, None, None, 'A file path or URL to a torrent file or a magnet link.'
        ),
        'files-wanted': Args(
            'array', 1, None, None, None, "A list of file id's that should be downloaded."
        ),
        'files-unwanted': Args(
            'array', 1, None, None, None, "A list of file id's that shouldn't be downloaded."
        ),
        'metainfo': Args(
            'string', 1, None, None, None, 'The content of a torrent file, base64 encoded.'
        ),
        'paused': Args(
            'boolean', 1, None, None, None, 'If True, does not start the transfer when added.'
        ),
        'peer-limit': Args('number', 1, None, None, None, 'Maximum number of peers allowed.'),
        'priority-high': Args(
            'array', 1, None, None, None, "A list of file id's that should have high priority."
        ),
        'priority-low': Args(
            'array', 1, None, None, None, "A list of file id's that should have low priority."
        ),
        'priority-normal': Args(
            'array', 1, None, None, None, "A list of file id's that should have normal priority."
        ),
    }
}

# Arguments for session methods
SESSION_ARGS = {
    'get': {
        'alt-speed-down': Args(
            'number', 5, None, None, None, 'Alternate session download speed limit (in Kib/s).'
        ),
        'alt-speed-enabled': Args(
            'boolean', 5, None, None, None,
            'True if alternate global download speed limiter is enabled.'
        ),
        'alt-speed-time-begin': Args(
            'number', 5, None, None, None,
            'Time when alternate speeds should be enabled. Minutes after midnight.'
        ),
        'alt-speed-time-enabled': Args(
            'boolean', 5, None, None, None, 'True if alternate speeds scheduling is enabled.'
        ),
        'alt-speed-time-end': Args(
            'number', 5, None, None, None,
            'Time when alternate speeds should be disabled. Minutes after midnight.'
        ),
        'alt-speed-time-day': Args(
            'number', 5, None, None, None, 'Days alternate speeds scheduling is enabled.'
        ),
        'alt-speed-up': Args(
            'number', 5, None, None, None, 'Alternate session upload speed limit (in Kib/s)'
        ),
        'blocklist-enabled': Args(
            'boolean', 5, None, None, None, 'True when blocklist is enabled.'
        ),
        'blocklist-size': Args('number', 5, None, None, None, 'Number of rules in the blocklist'),
        'blocklist-url': Args(
            'string', 11, None, None, None,
            'Location of the block list. Updated with blocklist-update.'
        ),
        'cache-size-mb': Args(
            'number', 10, None, None, None, 'The maximum size of the disk cache in MB'
        ),
        'config-dir': Args(
            'string', 8, None, None, None, 'location of transmissions configuration directory'
        ),
        'dht-enabled': Args('boolean', 6, None, None, None, 'True if DHT enabled.'),
        'download-dir': Args('string', 1, None, None, None, 'The download directory.'),
        'download-dir-free-space': Args(
            'number', 12, None, None, None, 'Free space in the download directory, in bytes'
        ),
        'download-queue-size': Args(
            'number', 14, None, None, None, 'Number of slots in the download queue.'
        ),
        'download-queue-enabled': Args(
            'boolean', 14, None, None, None, 'True if the download queue is enabled.'
        ),
        'encryption': Args(
            'string', 1, None, None, None,
            'Encryption mode, one of ``required``, ``preferred`` or ``tolerated``.'
        ),
        'idle-seeding-limit': Args(
            'number', 10, None, None, None, 'Seed inactivity limit in minutes.'
        ),
        'idle-seeding-limit-enabled': Args(
            'boolean', 10, None, None, None, 'True if the seed activity limit is enabled.'
        ),
        'incomplete-dir': Args(
            'string', 7, None, None, None,
            'The path to the directory for incomplete torrent transfer data.'
        ),
        'incomplete-dir-enabled': Args(
            'boolean', 7, None, None, None, 'True if the incomplete dir is enabled.'
        ),
        'lpd-enabled': Args(
            'boolean', 9, None, None, None, 'True if local peer discovery is enabled.'
        ),
        'peer-limit': Args('number', 1, 5, None, 'peer-limit-global', 'Maximum number of peers.'),
        'peer-limit-global': Args(
            'number', 5, None, 'peer-limit', None, 'Maximum number of peers.'
        ),
        'peer-limit-per-torrent': Args(
            'number', 5, None, None, None, 'Maximum number of peers per transfer.'
        ),
        'pex-allowed': Args('boolean', 1, 5, None, 'pex-enabled', 'True if PEX is allowed.'),
        'pex-enabled': Args('boolean', 5, None, 'pex-allowed', None, 'True if PEX is enabled.'),
        'port': Args('number', 1, 5, None, 'peer-port', 'Peer port.'),
        'peer-port': Args('number', 5, None, 'port', None, 'Peer port.'),
        'peer-port-random-on-start': Args(
            'boolean', 5, None, None, None, 'Enables randomized peer port on start of Transmission.'
        ),
        'port-forwarding-enabled': Args(
            'boolean', 1, None, None, None, 'True if port forwarding is enabled.'
        ),
        'queue-stalled-minutes': Args(
            'number', 14, None, None, None,
            'Number of minutes of idle that marks a transfer as stalled.'
        ),
        'queue-stalled-enabled': Args(
            'boolean', 14, None, None, None, 'True if stalled tracking of transfers is enabled.'
        ),
        'rename-partial-files': Args(
            'boolean', 8, None, None, None, 'True if ".part" is appended to incomplete files'
        ),
        'rpc-version': Args('number', 4, None, None, None, 'Transmission RPC API Version.'),
        'rpc-version-minimum': Args(
            'number', 4, None, None, None, 'Minimum accepted RPC API Version.'
        ),
        'script-torrent-done-enabled': Args(
            'boolean', 9, None, None, None, 'True if the done script is enabled.'
        ),
        'script-torrent-done-filename': Args(
            'string', 9, None, None, None,
            'Filename of the script to run when the transfer is done.'
        ),
        'seedRatioLimit': Args(
            'double', 5, None, None, None,
            'Seed ratio limit. 1.0 means 1:1 download and upload ratio.'
        ),
        'seedRatioLimited': Args(
            'boolean', 5, None, None, None, 'True if seed ration limit is enabled.'
        ),
        'seed-queue-size': Args(
            'number', 14, None, None, None, 'Number of slots in the upload queue.'
        ),
        'seed-queue-enabled': Args(
            'boolean', 14, None, None, None, 'True if upload queue is enabled.'
        ),
        'speed-limit-down': Args('number', 1, None, None, None, 'Download speed limit (in Kib/s).'),
        'speed-limit-down-enabled': Args(
            'boolean', 1, None, None, None, 'True if the download speed is limited.'
        ),
        'speed-limit-up': Args('number', 1, None, None, None, 'Upload speed limit (in Kib/s).'),
        'speed-limit-up-enabled': Args(
            'boolean', 1, None, None, None, 'True if the upload speed is limited.'
        ),
        'start-added-torrents': Args(
            'boolean', 9, None, None, None, 'When true uploaded torrents will start right away.'
        ),
        'trash-original-torrent-files': Args(
            'boolean', 9, None, None, None, 'When true added .torrent files will be deleted.'
        ),
        'units': Args(
            'object', 10, None, None, None, 'An object containing units for size and speed.'
        ),
        'utp-enabled': Args(
            'boolean', 13, None, None, None, 'True if Micro Transport Protocol (UTP) is enabled.'
        ),
        'version': Args('string', 3, None, None, None, 'Transmission version.'),
    },
    'set': {
        'alt-speed-down': Args(
            'number', 5, None, None, None, 'Alternate session download speed limit (in Kib/s).'
        ),
        'alt-speed-enabled': Args(
            'boolean', 5, None, None, None, 'Enables alternate global download speed limiter.'
        ),
        'alt-speed-time-begin': Args(
            'number', 5, None, None, None,
            'Time when alternate speeds should be enabled. Minutes after midnight.'
        ),
        'alt-speed-time-enabled': Args(
            'boolean', 5, None, None, None, 'Enables alternate speeds scheduling.'
        ),
        'alt-speed-time-end': Args(
            'number', 5, None, None, None,
            'Time when alternate speeds should be disabled. Minutes after midnight.'
        ),
        'alt-speed-time-day': Args(
            'number', 5, None, None, None, 'Enables alternate speeds scheduling these days.'
        ),
        'alt-speed-up': Args(
            'number', 5, None, None, None, 'Alternate session upload speed limit (in Kib/s).'
        ),
        'blocklist-enabled': Args('boolean', 5, None, None, None, 'Enables the block list'),
        'blocklist-url': Args(
            'string', 11, None, None, None,
            'Location of the block list. Updated with blocklist-update.'
        ),
        'cache-size-mb': Args(
            'number', 10, None, None, None, 'The maximum size of the disk cache in MB'
        ),
        'dht-enabled': Args('boolean', 6, None, None, None, 'Enables DHT.'),
        'download-dir': Args('string', 1, None, None, None, 'Set the session download directory.'),
        'download-queue-size': Args(
            'number', 14, None, None, None, 'Number of slots in the download queue.'
        ),
        'download-queue-enabled': Args('boolean', 14, None, None, None, 'Enables download queue.'),
        'encryption': Args(
            'string', 1, None, None, None,
            'Set the session encryption mode, one of ``required``, ``preferred`` or ``tolerated``.'
        ),
        'idle-seeding-limit': Args(
            'number', 10, None, None, None, 'The default seed inactivity limit in minutes.'
        ),
        'idle-seeding-limit-enabled': Args(
            'boolean', 10, None, None, None, 'Enables the default seed inactivity limit'
        ),
        'incomplete-dir': Args(
            'string', 7, None, None, None, 'The path to the directory of incomplete transfer data.'
        ),
        'incomplete-dir-enabled': Args(
            'boolean', 7, None, None, None,
            'Enables the incomplete transfer data directory. Otherwise data for incomplete transfers are stored in the download target.'
        ),
        'lpd-enabled': Args(
            'boolean', 9, None, None, None, 'Enables local peer discovery for public torrents.'
        ),
        'peer-limit': Args('number', 1, 5, None, 'peer-limit-global', 'Maximum number of peers.'),
        'peer-limit-global': Args(
            'number', 5, None, 'peer-limit', None, 'Maximum number of peers.'
        ),
        'peer-limit-per-torrent': Args(
            'number', 5, None, None, None, 'Maximum number of peers per transfer.'
        ),
        'pex-allowed': Args(
            'boolean', 1, 5, None, 'pex-enabled', 'Allowing PEX in public torrents.'
        ),
        'pex-enabled': Args(
            'boolean', 5, None, 'pex-allowed', None, 'Allowing PEX in public torrents.'
        ),
        'port': Args('number', 1, 5, None, 'peer-port', 'Peer port.'),
        'peer-port': Args('number', 5, None, 'port', None, 'Peer port.'),
        'peer-port-random-on-start': Args(
            'boolean', 5, None, None, None, 'Enables randomized peer port on start of Transmission.'
        ),
        'port-forwarding-enabled': Args('boolean', 1, None, None, None, 'Enables port forwarding.'),
        'rename-partial-files': Args(
            'boolean', 8, None, None, None, 'Appends ".part" to incomplete files'
        ),
        'queue-stalled-minutes': Args(
            'number', 14, None, None, None,
            'Number of minutes of idle that marks a transfer as stalled.'
        ),
        'queue-stalled-enabled': Args(
            'boolean', 14, None, None, None, 'Enable tracking of stalled transfers.'
        ),
        'script-torrent-done-enabled': Args(
            'boolean', 9, None, None, None, 'Whether or not to call the "done" script.'
        ),
        'script-torrent-done-filename': Args(
            'string', 9, None, None, None,
            'Filename of the script to run when the transfer is done.'
        ),
        'seed-queue-size': Args(
            'number', 14, None, None, None, 'Number of slots in the upload queue.'
        ),
        'seed-queue-enabled': Args('boolean', 14, None, None, None, 'Enables upload queue.'),
        'seedRatioLimit': Args(
            'double', 5, None, None, None,
            'Seed ratio limit. 1.0 means 1:1 download and upload ratio.'
        ),
        'seedRatioLimited': Args('boolean', 5, None, None, None, 'Enables seed ration limit.'),
        'speed-limit-down': Args('number', 1, None, None, None, 'Download speed limit (in Kib/s).'),
        'speed-limit-down-enabled': Args(
            'boolean', 1, None, None, None, 'Enables download speed limiting.'
        ),
        'speed-limit-up': Args('number', 1, None, None, None, 'Upload speed limit (in Kib/s).'),
        'speed-limit-up-enabled': Args(
            'boolean', 1, None, None, None, 'Enables upload speed limiting.'
        ),
        'start-added-torrents': Args(
            'boolean', 9, None, None, None, 'Added torrents will be started right away.'
        ),
        'trash-original-torrent-files': Args(
            'boolean', 9, None, None, None, 'The .torrent file of added torrents will be deleted.'
        ),
        'utp-enabled': Args(
            'boolean', 13, None, None, None, 'Enables Micro Transport Protocol (UTP).'
        ),
    },
}
