..
	Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
	Licensed under the MIT license.


:mod:`transmissionrpc` --- Module reference
###########################################

.. module:: transmissionrpc
.. moduleauthor:: Erik Svensson <erik.public@gmail.com>

This documentation will not describe all RPC fields in detail. Please refer to
the `RPC specification`_ for more information on RPC data.

.. _RPC specification: http://trac.transmissionbt.com/wiki/rpc

.. contents::
	:depth: 3

Exceptions
==========

.. autoclass:: TransmissionError

	.. attribute:: original

		The original exception.

.. autoclass:: HTTPHandlerError

	.. attribute:: url

		The requested url.

	.. attribute:: code

		HTTP error code.

	.. attribute:: message

		HTTP error message.

	.. attribute:: headers

		HTTP headers.

	.. attribute:: data

		HTTP data.

Torrent object
==============

Torrent is a class holding the information received from Transmission regarding a bittorrent transfer.

Attributes
----------

All fetched torrent fields are accessible through this class using attributes. The attributes use underscore instead of
hyphen in the names though. This class has a few convenience attributes using the torrent information.

Example:
::

	>>> import transmissionrpc
	>>> t = transmissionrpc.Torrent(None, {'id': 1, 'comment': 'My torrent', 'addedDate': 1232281019})
	>>> t.comment
	'My torrent'
	>>> t.date_added
	datetime.datetime(2009, 1, 18, 13, 16, 59)
	>>>

Transmission returns following fields.

=========================== ====== ==========================================================================================================
Argument                    RPC    Description
=========================== ====== ==========================================================================================================
``activityDate``            1 -    Last time of upload or download activity.
``addedDate``               1 -    The date when this torrent was first added.
``announceResponse``        1 - 7  The announce message from the tracker.
``announceURL``             1 - 7  Current announce URL.
``bandwidthPriority``       5 -    Bandwidth priority. Low (-1), Normal (0) or High (1).
``comment``                 1 -    Torrent comment.
``corruptEver``             1 -    Number of bytes of corrupt data downloaded.
``creator``                 1 -    Torrent creator.
``dateCreated``             1 -    Torrent creation date.
``desiredAvailable``        1 -    Number of bytes avalable and left to be downloaded.
``doneDate``                1 -    The date when the torrent finished downloading.
``downloadDir``             4 -    The directory path where the torrent is downloaded to.
``downloadLimit``           1 -    Download limit in Kbps.
``downloadLimitMode``       1 - 5  Download limit mode. 0 means global, 1 means signle, 2 unlimited.
``downloadLimited``         5 -    Download limit is enabled
``downloadedEver``          1 -    Number of bytes of good data downloaded.
``downloaders``             4 - 7  Number of downloaders.
``error``                   1 -    Kind of error. 0 means OK, 1 means tracker warning, 2 means tracker error, 3 means local error.
``errorString``             1 -    Error message.
``eta``                     1 -    Estimated number of seconds left when downloading or seeding. -1 means not available and -2 means unknown.
``fileStats``               5 -    Aray of file statistics containing bytesCompleted, wanted and priority.
``files``                   1 -    Array of file object containing key, bytesCompleted, length and name.
``hashString``              1 -    Hashstring unique for the torrent even between sessions.
``haveUnchecked``           1 -    Number of bytes of partial pieces.
``haveValid``               1 -    Number of bytes of checksum verified data.
``honorsSessionLimits``     5 -    True if session upload limits are honored
``id``                      1 -    Session unique torrent id.
``isFinished``              9 -    True if the torrent is finished. Downloaded and seeded.
``isPrivate``               1 -    True if the torrent is private.
``isStalled``               14 -   True if the torrent has stalled (been idle for a long time).
``lastAnnounceTime``        1 - 7  The time of the last announcement.
``lastScrapeTime``          1 - 7  The time af the last successful scrape.
``leechers``                1 - 7  Number of leechers.
``leftUntilDone``           1 -    Number of bytes left until the download is done.
``magnetLink``              7 -    The magnet link for this torrent.
``manualAnnounceTime``      1 -    The time until you manually ask for more peers.
``maxConnectedPeers``       1 -    Maximum of connected peers.
``metadataPercentComplete`` 7 -    Download progress of metadata. 0.0 to 1.0.
``name``                    1 -    Torrent name.
``nextAnnounceTime``        1 - 7  Next announce time.
``nextScrapeTime``          1 - 7  Next scrape time.
``peer_limit``              5 -    Maximum number of peers.
``peers``                   2 -    Array of peer objects.
``peersConnected``          1 -    Number of peers we are connected to.
``peersFrom``               1 -    Object containing download peers counts for different peer types.
``peersGettingFromUs``      1 -    Number of peers we are sending data to.
``peersKnown``              1 - 13 Number of peers that the tracker knows.
``peersSendingToUs``        1 -    Number of peers sending to us
``percentDone``             5 -    Download progress of selected files. 0.0 to 1.0.
``pieceCount``              1 -    Number of pieces.
``pieceSize``               1 -    Number of bytes in a piece.
``pieces``                  5 -    String with base64 encoded bitfield indicating finished pieces.
``priorities``              1 -    Array of file priorities.
``queuePosition``           14 -   The queue position.
``rateDownload``            1 -    Download rate in bps.
``rateUpload``              1 -    Upload rate in bps.
``recheckProgress``         1 -    Progress of recheck. 0.0 to 1.0.
``scrapeResponse``          1 - 7  Scrape response message.
``scrapeURL``               1 - 7  Current scrape URL
``seedIdleLimit``           10 -   Idle limit in minutes.
``seedIdleMode``            10 -   Use global (0), torrent (1), or unlimited (2) limit.
``seedRatioLimit``          5 -    Seed ratio limit.
``seedRatioMode``           5 -    Use global (0), torrent (1), or unlimited (2) limit.
``seeders``                 1 - 7  Number of seeders reported by the tracker.
``sizeWhenDone``            1 -    Size of the torrent download in bytes.
``startDate``               1 -    The date when the torrent was last started.
``status``                  1 -    Current status, see source
``swarmSpeed``              1 - 7  Estimated speed in Kbps in the swarm.
``timesCompleted``          1 - 7  Number of successful downloads reported by the tracker.
``torrentFile``             5 -    Path to .torrent file.
``totalSize``               1 -    Total size of the torrent in bytes
``trackerStats``            7 -    Array of object containing tracker statistics.
``trackers``                1 -    Array of tracker objects.
``uploadLimit``             1 -    Upload limit in Kbps
``uploadLimitMode``         1 - 5  Upload limit mode. 0 means global, 1 means signle, 2 unlimited.
``uploadLimited``           5 -    Upload limit enabled.
``uploadRatio``             1 -    Seed ratio.
``uploadedEver``            1 -    Number of bytes uploaded, ever.
``wanted``                  1 -    Array of booleans indicated wanted files.
``webseeds``                1 -    Array of webseeds objects
``webseedsSendingToUs``     1 -    Number of webseeds seeding to us.
=========================== ====== ==========================================================================================================

Mutators
--------

Some attributes can be changed, these are called mutators. These changes will be sent to the server when changed.
To reload information from Transmission use ``update()``.

Example:
::

	>>> import transmissionrpc
	>>> c = transmissionrpc.Client()
	>>> t = c.get_torrent(0)
	>>> t.peer_limit
	10
	>>> t.peer_limit = 20
	>>> t.update()
	>>> t.peer_limit
	20

Reference
---------

.. autoclass:: Torrent
	:members:

Session object
==============

Session is a class holding the session data for a Transmission session.

Attributes
----------

Access the session field can be done through attributes.
The attributes available are the same as the session arguments in the
Transmission RPC specification, but with underscore instead of hyphen.
``download-dir`` -> ``download_dir``.

Transmission returns following fields.

================================ ===== ================= ======================================================================
Argument                         RPC   Replaced by       Description
================================ ===== ================= ======================================================================
``alt_speed_down``               5 -                     Alternate session download speed limit (in Kib/s).
``alt_speed_enabled``            5 -                     True if alternate global download speed limiter is ebabled.
``alt_speed_time_begin``         5 -                     Time when alternate speeds should be enabled. Minutes after midnight.
``alt_speed_time_day``           5 -                     Days alternate speeds scheduling is enabled.
``alt_speed_time_enabled``       5 -                     True if alternate speeds scheduling is enabled.
``alt_speed_time_end``           5 -                     Time when alternate speeds should be disabled. Minutes after midnight.
``alt_speed_up``                 5 -                     Alternate session upload speed limit (in Kib/s)
``blocklist_enabled``            5 -                     True when blocklist is enabled.
``blocklist_size``               5 -                     Number of rules in the blocklist
``blocklist_url``                11 -                    Location of the block list. Updated with blocklist-update.
``cache_size_mb``                10 -                    The maximum size of the disk cache in MB
``config_dir``                   8 -                     location of transmissions configuration directory
``dht_enabled``                  6 -                     True if DHT enabled.
``download_dir``                 1 -                     The download directory.
``download_dir_free_space``      12 -                    Free space in the download directory, in bytes
``download_queue_enabled``       14 -                    True if the download queue is enabled.
``download_queue_size``          14 -                    Number of slots in the download queue.
``encryption``                   1 -                     Encryption mode, one of ``required``, ``preferred`` or ``tolerated``.
``idle_seeding_limit``           10 -                    Seed inactivity limit in minutes.
``idle_seeding_limit_enabled``   10 -                    True if the seed activity limit is enabled.
``incomplete_dir``               7 -                     The path to the directory for incomplete torrent transfer data.
``incomplete_dir_enabled``       7 -                     True if the incomplete dir is enabled.
``lpd_enabled``                  9 -                     True if local peer discovery is enabled.
``peer_limit``                   1 - 5 peer-limit-global Maximum number of peers.
``peer_limit_global``            5 -                     Maximum number of peers.
``peer_limit_per_torrent``       5 -                     Maximum number of peers per transfer.
``peer_port``                    5 -                     Peer port.
``peer_port_random_on_start``    5 -                     Enables randomized peer port on start of Transmission.
``pex_allowed``                  1 - 5 pex-enabled       True if PEX is allowed.
``pex_enabled``                  5 -                     True if PEX is enabled.
``port``                         1 - 5 peer-port         Peer port.
``port_forwarding_enabled``      1 -                     True if port forwarding is enabled.
``queue_stalled_enabled``        14 -                    True if stalled tracking of transfers is enabled.
``queue_stalled_minutes``        14 -                    Number of minutes of idle that marks a transfer as stalled.
``rename_partial_files``         8 -                     True if ".part" is appended to incomplete files
``rpc_version``                  4 -                     Transmission RPC API Version.
``rpc_version_minimum``          4 -                     Minimum accepted RPC API Version.
``script_torrent_done_enabled``  9 -                     True if the done script is enabled.
``script_torrent_done_filename`` 9 -                     Filename of the script to run when the transfer is done.
``seed_queue_enabled``           14 -                    True if upload queue is enabled.
``seed_queue_size``              14 -                    Number of slots in the upload queue.
``seedRatioLimit``               5 -                     Seed ratio limit. 1.0 means 1:1 download and upload ratio.
``seedRatioLimited``             5 -                     True if seed ration limit is enabled.
``speed_limit_down``             1 -                     Download speed limit (in Kib/s).
``speed_limit_down_enabled``     1 -                     True if the download speed is limited.
``speed_limit_up``               1 -                     Upload speed limit (in Kib/s).
``speed_limit_up_enabled``       1 -                     True if the upload speed is limited.
``start_added_torrents``         9 -                     When true uploaded torrents will start right away.
``trash_original_torrent_files`` 9 -                     When true added .torrent files will be deleted.
``units``                        10 -                    An object containing units for size and speed.
``utp_enabled``                  13 -                    True if Micro Transport Protocol (UTP) is enabled.
``version``                      3 -                     Transmission version.
================================ ===== ================= ======================================================================

Mutators
--------

Some attributes can be changed, these are called mutators. These changes will be sent to the server when changed.
To reload information from Transmission use ``update()``.

Reference
---------

.. autoclass:: Session
	:members:

Client object
=============

This class implements the JSON-RPC protocol to communicate with Transmission.

Torrent ids
-----------

Many functions in Client takes torrent id. A torrent id can either be id or
hashString. When supplying multiple id's it is possible to use a list mixed
with both id and hashString.

Timeouts
--------

In Python 2.6 it is possible to supply a timeout to a HTTP request. This is
accessible through transmissionrpc by either changing the timeout property of
a Client object or supply the named argument ``timeout`` in most methods of
Client. The default timeout is 30 seconds.

Reference
---------

.. autoclass:: Client
	:members:
