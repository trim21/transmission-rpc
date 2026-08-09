Migrating to v8
===============

Version 7.1 provides the replacement APIs needed for most v8 migrations. Run
your test suite with deprecation warnings treated as errors before upgrading::

    pytest -W error::DeprecationWarning

API replacements
----------------

Replace the following v7 APIs before upgrading:

* ``Torrent.hashString`` with ``Torrent.hash_string``.
* ``FileStat.bytesCompleted`` with ``FileStat.bytes_completed``.
* ``TransmissionError.rawResponse`` with ``TransmissionError.raw_response``.
* ``Client.add_torrent(bandwidthPriority=...)`` with ``bandwidth_priority``.
* ``Session.cache_size_mb`` and ``Client.set_session(cache_size_mb=...)`` with
  ``cache_size_mib``.
* ``Session.download_dir_free_space`` with ``Client.free_space(...)``.
* ``Client.start_torrent(..., bypass_queue=True)`` with
  ``Client.start_torrent_now(...)``.
* ``Client.start_all()`` with ``Client.start_torrent()`` without torrent IDs.
* ``transmission_rpc.utils.get_torrent_arguments`` with
  ``transmission_rpc.constants.get_torrent_arguments``.

``format_size`` and ``format_speed`` are removed without replacement. Move
formatting into application code or use a dedicated formatting package.

Other breaking changes
----------------------

The following APIs keep their names but intentionally change their return
semantics in v8. They do not have a cross-version compatibility API:

* ``Torrent.pieces`` returns ``BitMap`` instead of a base64 string.
* ``Torrent.tracker_list`` preserves tracker tiers instead of returning a flat
  list.
* ``Client.port_test()`` returns ``PortTestResult`` instead of ``bool``.

Version 8 requires Python 3.10 or newer and uses urllib3 instead of requests for
HTTP transport. Code which accesses private HTTP client attributes is not
supported across the upgrade.
