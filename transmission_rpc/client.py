# Copyright (c) 2020 littleya <me@littleya.com>
# Copyright (c) 2018-2020 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.

import os
import re
import json
import time
import base64
import string
import logging
import operator
from typing import TYPE_CHECKING, List, Union, Optional
from urllib.parse import urljoin, urlparse

import yarl
import requests
import requests.auth

from transmission_rpc.error import TransmissionError
from transmission_rpc.utils import (
    LOGGER, Field, rpc_bool, get_arguments, make_rpc_name, argument_value_convert
)
from transmission_rpc.session import Session
from transmission_rpc.torrent import Torrent
from transmission_rpc.constants import DEFAULT_TIMEOUT
from transmission_rpc.decorator import arg, replaced_by

valid_hash_char = string.digits + string.ascii_letters

if TYPE_CHECKING:
    from typing_extensions import Literal


def _parse_torrent_id(raw_torrent_id):
    if isinstance(raw_torrent_id, int):
        if raw_torrent_id >= 0:
            return raw_torrent_id
    elif isinstance(raw_torrent_id, str):
        if len(raw_torrent_id) != 40 or (set(raw_torrent_id) - set(valid_hash_char)):
            raise ValueError(f'torrent ids {raw_torrent_id} if not a valid sha1 hash')
        return raw_torrent_id
    elif isinstance(raw_torrent_id, Field):
        return _parse_torrent_ids(raw_torrent_id.value)
    raise ValueError(f'{raw_torrent_id} is not valid torrent id')


def _parse_torrent_ids(args):
    if args is None:
        return []
    if isinstance(args, int):
        return [_parse_torrent_id(args)]
    elif isinstance(args, str):
        if args == 'recently-active':
            return args
        return [_parse_torrent_id(args)]
    elif isinstance(args, (list, tuple)):
        return [_parse_torrent_id(item) for item in args]
    raise ValueError(f'Invalid torrent id {args}')


class Client:
    def __init__(
        self,
        *,
        protocol: "Literal['http', 'https']" = 'http',
        username: str = None,
        password: str = None,
        host: str = '127.0.0.1',
        port: int = 9091,
        path: str = '/transmission/',
        timeout: Union[int, float] = DEFAULT_TIMEOUT,
        logger=LOGGER
    ):
        if isinstance(logger, logging.Logger):
            self.logger = logger
        else:
            raise TypeError(
                'logger must be instance of `logging.Logger`, '
                'default: logging.getLogger(\'transmission-rpc\')'
            )
        self._query_timeout = timeout
        url = yarl.URL.build(
            scheme=protocol,
            user=username,
            password=password,
            host=host,
            port=port,
            path=urljoin(path, 'rpc')
        )
        self.url = str(url)
        self._sequence = 0
        self.session: Session = Session()
        self.session_id = 0
        self.server_version = None
        self.protocol_version: Optional[int] = None
        self._http_session = requests.Session()
        self.get_session()
        self.torrent_get_arguments = get_arguments('torrent-get', self.rpc_version)

    @property
    def timeout(self):
        """
        Get current timeout for HTTP queries.
        """
        return self._query_timeout

    @timeout.setter
    def timeout(self, value):
        """
        Set timeout for HTTP queries.
        """
        self._query_timeout = float(value)

    @timeout.deleter
    def timeout(self):
        """
        Reset the HTTP query timeout to the default.
        """
        self._query_timeout = DEFAULT_TIMEOUT

    @property
    def _http_header(self):
        return {'x-transmission-session-id': str(self.session_id)}

    def _http_query(self, query, timeout=None):
        """
        Query Transmission through HTTP.
        """
        request_count = 0
        if timeout is None:
            timeout = self.timeout
        while True:
            if request_count >= 10:
                raise TransmissionError('too much request, try enable logger to see what happened')
            self.logger.debug({
                'url': self.url,
                'headers': self._http_header,
                'data': json.loads(query),
                'timeout': timeout,
            })
            request_count += 1
            r = self._http_session.post(
                self.url, headers=self._http_header, json=json.loads(query), timeout=timeout
            )
            self.session_id = r.headers.get('X-Transmission-Session-Id', 0)
            self.logger.debug(r.text)
            if r.status_code == 401:
                print(r.request.headers)
                raise TransmissionError('transmission daemon require auth', original=r)
            if r.status_code != 409:
                return r.text

    def _request(self, method, arguments=None, ids=None, require_ids=False, timeout=None):
        """
        Send json-rpc request to Transmission using http POST
        :type arguments: object
        :type method: str
        """
        if not isinstance(method, str):
            raise ValueError('request takes method as string')
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise ValueError('request takes arguments as dict')
        arguments = {key.replace('_', '-'): value for key, value in arguments.items()}
        ids = _parse_torrent_ids(ids)
        if len(ids) > 0:
            arguments['ids'] = ids
        elif require_ids:
            raise ValueError('request require ids')

        query = json.dumps({'tag': self._sequence, 'method': method, 'arguments': arguments})
        self._sequence += 1
        start = time.time()
        http_data = self._http_query(query, timeout)
        elapsed = time.time() - start
        self.logger.info('http request took %.3f s' % elapsed)

        try:
            data = json.loads(http_data)
        except ValueError as error:
            self.logger.error('Error: ' + str(error))
            self.logger.error('Request: \"%s\"' % query)
            self.logger.error('HTTP data: \"%s\"' % http_data)
            raise ValueError from error

        self.logger.debug(json.dumps(data, indent=2))
        if 'result' in data:
            if data['result'] != 'success':
                raise TransmissionError('Query failed with result \"%s\".' % (data['result']))
        else:
            raise TransmissionError('Query failed without result.')

        results = {}
        if method == 'torrent-get':
            for item in data['arguments']['torrents']:
                results[item['id']] = Torrent(self, item)
                if self.protocol_version == 2 and 'peers' not in item:
                    self.protocol_version = 1
        elif method == 'torrent-add':
            item = None
            if 'torrent-added' in data['arguments']:
                item = data['arguments']['torrent-added']
            elif 'torrent-duplicate' in data['arguments']:
                item = data['arguments']['torrent-duplicate']
            if item:
                results[item['id']] = Torrent(self, item)
            else:
                raise TransmissionError('Invalid torrent-add response.')
        elif method == 'session-get':
            self._update_session(data['arguments'])
        elif method == 'session-stats':
            # older versions of T has the return data in "session-stats"
            if 'session-stats' in data['arguments']:
                self._update_session(data['arguments']['session-stats'])
            else:
                self._update_session(data['arguments'])
        elif method in ('port-test', 'blocklist-update', 'free-space', 'torrent-rename-path'):
            results = data['arguments']
        else:
            return None

        return results

    def _update_session(self, data):
        """
        Update session data.
        """
        if self.session:
            self.session.from_request(data)
        else:
            self.session = Session(self, data)

    def _update_server_version(self):
        """Decode the Transmission version string, if available."""
        if self.server_version is None:
            version_major = 1
            version_minor = 30
            version_changeset = 0
            version_parser = re.compile(r'(\d).(\d+) \((\d+)\)')
            if hasattr(self.session, 'version'):
                match = version_parser.match(self.session.version)
                if match:
                    version_major = int(match.group(1))
                    version_minor = int(match.group(2))
                    version_changeset = match.group(3)
            self.server_version = (version_major, version_minor, version_changeset)

    @property
    def rpc_version(self) -> int:
        """
        Get the Transmission RPC version. Trying to deduct if the server don't have a version value.
        """
        if self.protocol_version is None:
            # Ugly fix for 2.20 - 2.22 reporting rpc-version 11, but having new arguments
            if self.server_version and (
                self.server_version[0] == 2 and self.server_version[1] in [20, 21, 22]
            ):
                self.protocol_version = 12
            # Ugly fix for 2.12 reporting rpc-version 10, but having new arguments
            elif self.server_version and (
                self.server_version[0] == 2 and self.server_version[1] == 12
            ):
                self.protocol_version = 11
            elif hasattr(self.session, 'rpc_version'):
                self.protocol_version = self.session.rpc_version
            elif hasattr(self.session, 'version'):
                self.protocol_version = 3
            else:
                self.protocol_version = 2
        return self.protocol_version

    def _rpc_version_warning(self, version):
        """
        Add a warning to the log if the Transmission RPC version is lower then the provided version.
        """
        if self.rpc_version < version:
            self.logger.warning(
                'Using feature not supported by server. RPC version for server %d, feature introduced in %d.'
                % (self.rpc_version, version)
            )

    @arg('bandwidthPriority', 8)
    @arg('cookies', 13)
    def add_torrent(self, torrent, timeout=None, **kwargs):
        """
        Add torrent to transfers list. Takes a uri to a torrent or base64 encoded torrent data in ``torrent``.
        You can find examples in test code
        `tests/test_client.py <https://github.com/Trim21/transmission-rpc/blob/master/tests/test_client.py>`_

        Additional arguments are:

        ===================== ===== =========== =============================================================
        Argument              RPC   Replaced by Description
        ===================== ===== =========== =============================================================
        ``bandwidthPriority`` 8 -               Priority for this transfer.
        ``cookies``           13 -              One or more HTTP cookie(s).
        ``download_dir``      1 -               The directory where the downloaded contents will be saved in.
        ``files_unwanted``    1 -               A list of file id's that shouldn't be downloaded.
        ``files_wanted``      1 -               A list of file id's that should be downloaded.
        ``paused``            1 -               If True, does not start the transfer when added.
        ``peer_limit``        1 -               Maximum number of peers allowed.
        ``priority_high``     1 -               A list of file id's that should have high priority.
        ``priority_low``      1 -               A list of file id's that should have low priority.
        ``priority_normal``   1 -               A list of file id's that should have normal priority.
        ===================== ===== =========== =============================================================

        Returns a Torrent object with the fields.
        """
        if torrent is None:
            raise ValueError('add_torrent requires data or a URI.')
        torrent_data = None
        is_url = False
        # torrent is a str, may be a url
        if isinstance(torrent, str):
            parsed_uri = urlparse(torrent)
            # torrent starts with file, read from local disk and encode it to base64 url.
            if parsed_uri.scheme in ['file']:
                filepath = torrent
                # uri decoded different on linux / windows ?
                if len(parsed_uri.path) > 0:
                    filepath = parsed_uri.path
                elif len(parsed_uri.netloc) > 0:
                    filepath = parsed_uri.netloc
                with open(filepath, 'rb') as torrent_file:
                    torrent_data = base64.b64encode(torrent_file.read()).decode('utf-8')
            elif parsed_uri.scheme in ['https', 'http', 'magnet']:
                is_url = True
            if (not is_url) and (not torrent_data):
                # base64 encoded file content
                might_be_base64 = False
                try:
                    # check if this is base64 data
                    base64.b64decode(torrent.encode('utf-8'), validate=True)
                    might_be_base64 = True
                except Exception:
                    pass
                if might_be_base64:
                    torrent_data = torrent

        # maybe a file, try read content and encode it.
        elif hasattr(torrent, 'read'):
            torrent_data = base64.b64encode(torrent.read()).decode('utf-8')

        if torrent_data:
            args = {'metainfo': torrent_data}
        else:
            args = {'filename': torrent}

        for key, value in kwargs.items():
            argument = make_rpc_name(key)
            (arg, val) = argument_value_convert('torrent-add', argument, value, self.rpc_version)
            args[arg] = val
        return list(self._request('torrent-add', args, timeout=timeout).values())[0]

    def remove_torrent(self, ids, delete_data=False, timeout=None):
        """
        remove torrent(s) with provided id(s). Local data is removed if
        delete_data is True, otherwise not.
        """
        self._rpc_version_warning(3)
        self._request(
            'torrent-remove', {'delete-local-data': rpc_bool(delete_data)},
            ids,
            True,
            timeout=timeout
        )

    def start_torrent(self, ids, bypass_queue=False, timeout=None):
        """Start torrent(s) with provided id(s)"""
        method = 'torrent-start'
        if bypass_queue and self.rpc_version >= 14:
            method = 'torrent-start-now'
        self._request(method, {}, ids, True, timeout=timeout)

    def start_all(self, bypass_queue=False, timeout=None):
        """Start all torrents respecting the queue order"""
        torrent_list = self.get_torrents()
        method = 'torrent-start'
        if self.rpc_version >= 14:
            if bypass_queue:
                method = 'torrent-start-now'
            torrent_list = sorted(torrent_list, key=operator.attrgetter('queuePosition'))
        ids = [x.id for x in torrent_list]
        self._request(method, {}, ids, True, timeout=timeout)

    def stop_torrent(self, ids, timeout=None):
        """stop torrent(s) with provided id(s)"""
        self._request('torrent-stop', {}, ids, True, timeout=timeout)

    def verify_torrent(self, ids, timeout=None):
        """verify torrent(s) with provided id(s)"""
        self._request('torrent-verify', {}, ids, True, timeout=timeout)

    def reannounce_torrent(self, ids, timeout=None):
        """Reannounce torrent(s) with provided id(s)"""
        self._rpc_version_warning(5)
        self._request('torrent-reannounce', {}, ids, True, timeout=timeout)

    def get_torrent(self, torrent_id, arguments=None, timeout=None):
        """
        Get information for torrent with provided id.
        ``arguments`` contains a list of field names to be returned, when None
        all fields are requested. See the Torrent class for more information.

        Returns a Torrent object with the requested fields.
        """
        if not arguments:
            arguments = self.torrent_get_arguments
        torrent_id = _parse_torrent_id(torrent_id)
        if torrent_id is None:
            raise ValueError('Invalid id')
        result = self._request(
            'torrent-get', {'fields': arguments}, torrent_id, require_ids=True, timeout=timeout
        )
        if torrent_id in result:
            return result[torrent_id]
        else:
            for torrent in result.values():
                if torrent.hashString == torrent_id:
                    return torrent
            raise KeyError('Torrent not found in result')

    def get_torrents(self, ids=None, arguments=None, timeout=None) -> List[Torrent]:
        """
        Get information for torrents with provided ids. For more information see get_torrent.

        Returns a list of Torrent object.
        :type ids: Union[int, str]
        :rtype : list[Torrent]
        """
        if not arguments:
            arguments = self.torrent_get_arguments
        return list(
            self._request('torrent-get', {'fields': arguments}, ids, timeout=timeout).values()
        )

    def get_files(self, ids=None, timeout=None):
        """
        Get list of files for provided torrent id(s). If ids is empty,
        information for all torrents are fetched. This function returns a dictionary
        for each requested torrent id holding the information about the files.

        ::

                {
                        <torrent id>: {
                                <file id>: {
                                        'name': <file name>,
                                        'size': <file size in bytes>,
                                        'completed': <bytes completed>,
                                        'priority': <priority ('high'|'normal'|'low')>,
                                        'selected': <selected for download (True|False)>
                                }

                                ...
                        }

                        ...
                }
        """
        fields = ['id', 'name', 'hashString', 'files', 'priorities', 'wanted']
        request_result = self._request('torrent-get', {'fields': fields}, ids, timeout=timeout)
        result = {}
        for tid, torrent in request_result.items():
            result[tid] = torrent.files()
        return result

    def set_files(self, items, timeout=None):
        """
        Set file properties. Takes a dictionary with similar contents as the result
        of `get_files`.

        ::

                {
                        <torrent id>: {
                                <file id>: {
                                        'priority': <priority ('high'|'normal'|'low')>,
                                        'selected': <selected for download (True|False)>
                                }

                                ...
                        }

                        ...
                }
        """
        if not isinstance(items, dict):
            raise ValueError('Invalid file description')
        for tid, files in items.items():
            if not isinstance(files, dict):
                continue
            wanted = []
            unwanted = []
            high = []
            normal = []
            low = []
            for fid, file_desc in files.items():
                if not isinstance(file_desc, dict):
                    continue
                if 'selected' in file_desc and file_desc['selected']:
                    wanted.append(fid)
                else:
                    unwanted.append(fid)
                if 'priority' in file_desc:
                    if file_desc['priority'] == 'high':
                        high.append(fid)
                    elif file_desc['priority'] == 'normal':
                        normal.append(fid)
                    elif file_desc['priority'] == 'low':
                        low.append(fid)
            args = {'timeout': timeout}
            if len(high) > 0:
                args['priority_high'] = high
            if len(normal) > 0:
                args['priority_normal'] = normal
            if len(low) > 0:
                args['priority_low'] = low
            if len(wanted) > 0:
                args['files_wanted'] = wanted
            if len(unwanted) > 0:
                args['files_unwanted'] = unwanted
            self.change_torrent([tid], **args)

    @arg('bandwidthPriority', 5)
    @arg('downloadLimit', 5)
    @arg('downloadLimited', 5)
    @arg('honorsSessionLimits', 5)
    @arg('queuePosition', 14)
    @arg('seedIdleLimit', 10)
    @arg('seedIdleMode', 10)
    @arg('downloadLimit', 5)
    @arg('downloadLimited', 5)
    @arg('uploadLimit', 5)
    @arg('uploadLimited', 5)
    @arg('trackerAdd', 10)
    @arg('trackerRemove', 10)
    @arg('trackerReplace', 10)
    @arg('uploadLimit', 5)
    @arg('uploadLimited', 5)
    def change_torrent(self, ids, timeout=None, **kwargs):
        """
        Change torrent parameters for the torrent(s) with the supplied id's. The
        parameters are:

        ============================ ===== =============== =============================================================
        Argument                     RPC   Replaced by     Description
        ============================ ===== =============== =============================================================
        ``bandwidthPriority``        5 -                   Priority for this transfer.
        ``downloadLimit``            5 -                   Set the speed limit for download in Kib/s.
        ``downloadLimited``          5 -                   Enable download speed limiter.
        ``files_unwanted``           1 -                   A list of file id's that shouldn't be downloaded.
        ``files_wanted``             1 -                   A list of file id's that should be downloaded.
        ``honorsSessionLimits``      5 -                   Enables or disables the transfer
                                                           to honour the upload limit set in the session.
        ``location``                 1 -                   Local download location.
        ``peer_limit``               1 -                   The peer limit for the torrents.
        ``priority_high``            1 -                   A list of file id's that should have high priority.
        ``priority_low``             1 -                   A list of file id's that should have normal priority.
        ``priority_normal``          1 -                   A list of file id's that should have low priority.
        ``queuePosition``            14 -                  Position of this transfer in its queue.
        ``seedIdleLimit``            10 -                  Seed inactivity limit in minutes.
        ``seedIdleMode``             10 -                  Seed inactivity mode. 0 = Use session limit,
                                                           1 = Use transfer limit, 2 = Disable limit.
        ``seedRatioLimit``           5 -                   Seeding ratio.
        ``seedRatioMode``            5 -                   Which ratio to use. 0 = Use session limit,
                                                           1 = Use transfer limit, 2 = Disable limit.
        ``speed_limit_down``         1 - 5 downloadLimit   Set the speed limit for download in Kib/s.
        ``speed_limit_down_enabled`` 1 - 5 downloadLimited Enable download speed limiter.
        ``speed_limit_up``           1 - 5 uploadLimit     Set the speed limit for upload in Kib/s.
        ``speed_limit_up_enabled``   1 - 5 uploadLimited   Enable upload speed limiter.
        ``trackerAdd``               10 -                  Array of string with announce URLs to add.
        ``trackerRemove``            10 -                  Array of ids of trackers to remove.
        ``trackerReplace``           10 -                  Array of (id, url) tuples
                                                           where the announce URL should be replaced.
        ``uploadLimit``              5 -                   Set the speed limit for upload in Kib/s.
        ``uploadLimited``            5 -                   Enable upload speed limiter.
        ============================ ===== =============== =============================================================

        .. NOTE::
           transmission_rpc will try to automatically fix argument errors.
        """
        args = {}
        for key, value in kwargs.items():
            argument = make_rpc_name(key)
            (arg, val) = argument_value_convert('torrent-set', argument, value, self.rpc_version)
            args[arg] = val

        if len(args) > 0:
            self._request('torrent-set', args, ids, True, timeout=timeout)
        else:
            ValueError('No arguments to set')

    def move_torrent_data(self, ids, location, timeout=None):
        """Move torrent data to the new location."""
        self._rpc_version_warning(6)
        args = {'location': location, 'move': True}
        self._request('torrent-set-location', args, ids, True, timeout=timeout)

    def locate_torrent_data(self, ids, location, timeout=None):
        """Locate torrent data at the provided location."""
        self._rpc_version_warning(6)
        args = {'location': location, 'move': False}
        self._request('torrent-set-location', args, ids, True, timeout=timeout)

    def rename_torrent_path(self, torrent_id, location, name, timeout=None):
        """
        Rename directory and/or files for torrent.
        Remember to use get_torrent or get_torrents to update your file information.
        """
        self._rpc_version_warning(15)
        torrent_id = _parse_torrent_id(torrent_id)
        if torrent_id is None:
            raise ValueError('Invalid id')
        dirname = os.path.dirname(name)
        if len(dirname) > 0:
            raise ValueError('Target name cannot contain a path delimiter')
        args = {'path': location, 'name': name}
        result = self._request('torrent-rename-path', args, torrent_id, True, timeout=timeout)
        return (result['path'], result['name'])

    def queue_top(self, ids, timeout=None):
        """Move transfer to the top of the queue."""
        self._rpc_version_warning(14)
        self._request('queue-move-top', ids=ids, require_ids=True, timeout=timeout)

    def queue_bottom(self, ids, timeout=None):
        """Move transfer to the bottom of the queue."""
        self._rpc_version_warning(14)
        self._request('queue-move-bottom', ids=ids, require_ids=True, timeout=timeout)

    def queue_up(self, ids, timeout=None):
        """Move transfer up in the queue."""
        self._rpc_version_warning(14)
        self._request('queue-move-up', ids=ids, require_ids=True, timeout=timeout)

    def queue_down(self, ids, timeout=None):
        """Move transfer down in the queue."""
        self._rpc_version_warning(14)
        self._request('queue-move-down', ids=ids, require_ids=True, timeout=timeout)

    def get_session(self, timeout=None):
        """
        Get session parameters. See the Session class for more information.
        """
        self._request('session-get', timeout=timeout)
        self._update_server_version()
        return self.session

    @arg('alt_speed_down', 5)
    @arg('alt_speed_enabled', 5)
    @arg('alt_speed_time_begin', 5)
    @arg('alt_speed_time_day', 5)
    @arg('alt_speed_time_enabled', 5)
    @arg('alt_speed_time_end', 5)
    @arg('alt_speed_up', 5)
    @arg('blocklist_enabled', 5)
    @arg('blocklist_url', 11)
    @arg('cache_size_mb', 10)
    @arg('dht_enabled', 6)
    @arg('download_dir', 1)
    @arg('download_queue_enabled', 14)
    @arg('download_queue_size', 14)
    @arg('encryption', 1)
    @arg('idle_seeding_limit', 10)
    @arg('idle_seeding_limit_enabled', 10)
    @arg('incomplete_dir', 7)
    @arg('incomplete_dir_enabled', 7)
    @arg('lpd_enabled', 9)
    @arg('peer_limit', 1)
    @arg('peer_limit_global', 5)
    @arg('peer_limit_per_torrent', 5)
    @arg('peer_port', 5)
    @arg('peer_port_random_on_start', 5)
    @arg('pex_allowed', 1)
    @replaced_by('pex_allowed', 'pex_enabled', 5)
    @arg('pex_enabled', 5)
    @arg('port', 1)
    @arg('port_forwarding_enabled', 1)
    @arg('queue_stalled_enabled', 14)
    @arg('queue_stalled_minutes', 14)
    @arg('rename_partial_files', 8)
    @arg('script_torrent_done_enabled', 9)
    @arg('script_torrent_done_filename', 9)
    @arg('seed_queue_enabled', 14)
    @arg('seed_queue_size', 14)
    @arg('seedRatioLimit', 5)
    @arg('seedRatioLimited', 5)
    @arg('speed_limit_down', 1)
    @arg('speed_limit_down_enabled', 1)
    @arg('speed_limit_up', 1)
    @arg('speed_limit_up_enabled', 1)
    @arg('start_added_torrents', 9)
    @arg('trash_original_torrent_files', 9)
    @arg('utp_enabled', 13)
    def set_session(self, timeout=None, **kwargs):
        """
    Set session parameters. The parameters are:

    ================================ ===== ================= ===========================================================
    Argument                         RPC   Replaced by       Description
    ================================ ===== ================= ===========================================================
    ``alt_speed_down``               5 -                     Alternate session download speed limit (in Kib/s).
    ``alt_speed_enabled``            5 -                     Enables alternate global download speed limiter.
    ``alt_speed_time_begin``         5 -                        Time when alternate speeds should be enabled.
                                                                Minutes after midnight.
    ``alt_speed_time_day``           5 -                     Enables alternate speeds scheduling these days.
    ``alt_speed_time_enabled``       5 -                     Enables alternate speeds scheduling.
    ``alt_speed_time_end``           5 -                         Time when alternate speeds should be disabled.
                                                                 Minutes after midnight.
    ``alt_speed_up``                 5 -                     Alternate session upload speed limit (in Kib/s).
    ``blocklist_enabled``            5 -                     Enables the block list
    ``blocklist_url``                11 -                       Location of the block list.
                                                                Updated with blocklist-update.
    ``cache_size_mb``                10 -                    The maximum size of the disk cache in MB
    ``dht_enabled``                  6 -                     Enables DHT.
    ``download_dir``                 1 -                     Set the session download directory.
    ``download_queue_enabled``       14 -                    Enables download queue.
    ``download_queue_size``          14 -                    Number of slots in the download queue.
    ``encryption``                   1 -                         Set the session encryption mode, one of ``required``,
                                                                 ``preferred`` or ``tolerated``.
    ``idle_seeding_limit``           10 -                    The default seed inactivity limit in minutes.
    ``idle_seeding_limit_enabled``   10 -                    Enables the default seed inactivity limit
    ``incomplete_dir``               7 -                     The path to the directory of incomplete transfer data.
    ``incomplete_dir_enabled``       7 -                         Enables the incomplete transfer data directory.
                                                                 Otherwise data for incomplete transfers are stored in
                                                                 the download target.
    ``lpd_enabled``                  9 -                     Enables local peer discovery for public torrents.
    ``peer_limit``                   1 - 5 peer-limit-global Maximum number of peers.
    ``peer_limit_global``            5 -                     Maximum number of peers.
    ``peer_limit_per_torrent``       5 -                     Maximum number of peers per transfer.
    ``peer_port``                    5 -                     Peer port.
    ``peer_port_random_on_start``    5 -                     Enables randomized peer port on start of Transmission.
    ``pex_allowed``                  1 - 5 pex-enabled       Allowing PEX in public torrents.
    ``pex_enabled``                  5 -                     Allowing PEX in public torrents.
    ``port``                         1 - 5 peer-port         Peer port.
    ``port_forwarding_enabled``      1 -                     Enables port forwarding.
    ``queue_stalled_enabled``        14 -                    Enable tracking of stalled transfers.
    ``queue_stalled_minutes``        14 -                    Number of minutes of idle that marks a transfer as stalled.
    ``rename_partial_files``         8 -                     Appends ".part" to incomplete files
    ``script_torrent_done_enabled``  9 -                     Whether or not to call the "done" script.
    ``script_torrent_done_filename`` 9 -                     Filename of the script to run when the transfer is done.
    ``seed_queue_enabled``           14 -                    Enables upload queue.
    ``seed_queue_size``              14 -                    Number of slots in the upload queue.
    ``seedRatioLimit``               5 -                     Seed ratio limit. 1.0 means 1:1 download and upload ratio.
    ``seedRatioLimited``             5 -                     Enables seed ration limit.
    ``speed_limit_down``             1 -                     Download speed limit (in Kib/s).
    ``speed_limit_down_enabled``     1 -                     Enables download speed limiting.
    ``speed_limit_up``               1 -                     Upload speed limit (in Kib/s).
    ``speed_limit_up_enabled``       1 -                     Enables upload speed limiting.
    ``start_added_torrents``         9 -                     Added torrents will be started right away.
    ``trash_original_torrent_files`` 9 -                     The .torrent file of added torrents will be deleted.
    ``utp_enabled``                  13 -                    Enables Micro Transport Protocol (UTP).
    ================================ ===== ================= ===========================================================

    .. NOTE::
       transmission_rpc will try to automatically fix argument errors.
        """
        args = {}
        for key, value in kwargs.items():
            if key == 'encryption' and value not in ['required', 'preferred', 'tolerated']:
                raise ValueError('Invalid encryption value')
            argument = make_rpc_name(key)
            (arg, val) = argument_value_convert('session-set', argument, value, self.rpc_version)
            args[arg] = val
        if len(args) > 0:
            self._request('session-set', args, timeout=timeout)

    def blocklist_update(self, timeout=None):
        """Update block list. Returns the size of the block list."""
        self._rpc_version_warning(5)
        result = self._request('blocklist-update', timeout=timeout)
        if 'blocklist-size' in result:
            return result['blocklist-size']
        return None

    def port_test(self, timeout=None):
        """
        Tests to see if your incoming peer port is accessible from the
        outside world.
        """
        self._rpc_version_warning(5)
        result = self._request('port-test', timeout=timeout)
        if 'port-is-open' in result:
            return result['port-is-open']
        return None

    def free_space(self, path, timeout=None):
        """
        Get the amount of free space (in bytes) at the provided location.
        """
        self._rpc_version_warning(15)
        result = self._request('free-space', {'path': path}, timeout=timeout)
        if result['path'] == path:
            return result['size-bytes']
        return None

    def session_stats(self, timeout=None):
        """Get session statistics"""
        self._request('session-stats', timeout=timeout)
        return self.session

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._http_session.close()
