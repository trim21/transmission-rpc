Migrating to v8
===============

Version 7.0.12 provides the replacement APIs needed for most v8 migrations.
Install it first and run your test suite with deprecation warnings treated as
errors before upgrading::

    pip install "transmission-rpc==7.0.12"
    pytest -W error::DeprecationWarning

Version 8 removes the deprecated aliases. There is no 7.1 release.

API replacements
----------------

Replace the following v7 APIs before upgrading:

* ``Torrent.hashString`` with ``Torrent.hash_string``.
* ``Torrent.into_hash`` with ``Torrent.info_hash``.
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
* ``Client.rpc_version`` with ``Client.get_session().rpc_version``.
* ``Client.semver_version`` with ``Client.get_session().rpc_version_semver``.
* ``Client.server_version`` with ``Client.get_session().version``.
* ``Client.raw_session`` with ``Client.get_session()``.
* ``Client.torrent_get_arguments`` with
  ``transmission_rpc.constants.get_torrent_arguments(...)``.
* ``Client.url`` and ``Client.session_id`` have no replacement; they were
  internal properties.

``format_size`` and ``format_speed`` are removed without replacement. Move
formatting into application code or use a dedicated formatting package.

``Torrent.get_files()`` raises ``KeyError`` when the ``files`` field was not
fetched. Request ``files`` (or omit the arguments filter) before calling it.

Other breaking changes
----------------------

The following APIs keep their names but intentionally change their return
semantics in v8. They do not have a cross-version compatibility API:

* ``Torrent.pieces`` returns ``BitMap`` instead of a base64 string.
* ``Torrent.tracker_list`` preserves tracker tiers as ``list[list[str]]``
  instead of a flat ``list[str]``. Flatten the result when tier information is
  not needed::

      [url for tier in torrent.tracker_list for url in tier]

* ``Client.port_test()`` returns ``PortTestResult`` instead of ``bool``. Use
  ``.port_is_open``.

``Torrent.progress`` is rounded down, so an unfinished torrent never reports
``100.0``. To test for completion, use ``left_until_done == 0``.

Raw RPC dictionaries on ``Container`` subclasses (``Torrent.fields``,
``Session.fields``, ...) use snake_case names when talking to Transmission 4.1+
JSON-RPC 2.0. Public properties already handle both naming schemes. Code that
reads keys such as ``hashString`` or ``percentDone`` from ``.fields`` directly
should switch to the corresponding properties.

Version 8 requires Python 3.10 or newer and uses urllib3 instead of requests for
HTTP transport. ``TransmissionError.original`` is now a urllib3 response, not a
``requests.Response``. Code which accesses private HTTP client attributes is not
supported across the upgrade.
