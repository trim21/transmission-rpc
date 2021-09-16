# Copyright (c) 2020 Trim21 <i@trim21.me>
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.
# pylint: disable=C0103
import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Union, Optional

from transmission_rpc.utils import format_timedelta
from transmission_rpc.constants import PRIORITY, IDLE_LIMIT, RATIO_LIMIT
from transmission_rpc.lib_types import File, Field, _Timeout

if TYPE_CHECKING:
    from transmission_rpc.client import Client


def get_status_old(code: int) -> str:
    """Get the torrent status using old status codes"""
    mapping = {
        (1 << 0): "check pending",
        (1 << 1): "checking",
        (1 << 2): "downloading",
        (1 << 3): "seeding",
        (1 << 4): "stopped",
    }
    return mapping[code]


_STATUS_NEW_MAPPING = {
    0: "stopped",
    1: "check pending",
    2: "checking",
    3: "download pending",
    4: "downloading",
    5: "seed pending",
    6: "seeding",
}


def get_status_new(code: int) -> str:
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


class Torrent:
    """
    Torrent is a class holding the data received from Transmission regarding a bittorrent transfer.

    All fetched torrent fields are accessible through this class using attributes.
    This class has a few convenience properties using the torrent data.
    """

    def __init__(self, client: "Client", fields: Dict[str, Any]):
        if "id" not in fields:
            raise ValueError("Torrent requires an id")
        self._fields: Dict[str, Field] = {}
        self._update_fields(fields)
        self._incoming_pending = False
        self._outgoing_pending = False
        self._client = client

    @property
    def id(self) -> int:
        """Returns the id for this torrent"""
        return self._fields["id"].value

    def _get_name_string(self) -> Optional[str]:
        """Get the name"""
        name = None
        # try to find name
        if "name" in self._fields:
            name = self._fields["name"].value
        return name

    def __repr__(self) -> str:
        tid = self._fields["id"].value
        name = self._get_name_string()
        if name is not None:
            return f'<Torrent {tid} "{name}">'
        return f"<Torrent {tid}>"

    def __str__(self) -> str:
        name = self._get_name_string()
        if name is not None:
            return f'Torrent "{name}"'
        return "Torrent"

    def __copy__(self) -> "Torrent":
        return Torrent(self._client, self._fields)

    def __getattr__(self, name: str) -> Any:
        try:
            return self._fields[name].value
        except KeyError:
            raise AttributeError("No attribute %s" % name) from None

    def _rpc_version(self) -> int:
        """Get the Transmission RPC API version."""
        if self._client:
            return self._client.rpc_version
        return 2

    def _dirty_fields(self) -> List[str]:
        """Enumerate changed fields"""
        outgoing_keys = [
            "bandwidthPriority",
            "downloadLimit",
            "downloadLimited",
            "peer_limit",
            "queuePosition",
            "seedIdleLimit",
            "seedIdleMode",
            "seedRatioLimit",
            "seedRatioMode",
            "uploadLimit",
            "uploadLimited",
        ]
        fields = []
        for key in outgoing_keys:
            if key in self._fields and self._fields[key].dirty:
                fields.append(key)
        return fields

    def _push(self) -> None:
        """Push changed fields to the server"""
        dirty = self._dirty_fields()
        args = {}
        for key in dirty:
            args[key] = self._fields[key].value
            self._fields[key] = self._fields[key]._replace(dirty=False)
        if len(args) > 0:
            self._client.change_torrent(self.id, **args)

    def _update_fields(self, other: Union["Torrent", Dict[str, Any]]) -> None:
        """
        Update the torrent data from a Transmission JSON-RPC arguments dictionary
        """
        if isinstance(other, dict):
            for key, value in other.items():
                self._fields[key.replace("-", "_")] = Field(value, False)
        elif isinstance(other, Torrent):
            for key in list(other._fields.keys()):
                self._fields[key] = Field(other._fields[key].value, False)
        else:
            raise ValueError("Cannot update with supplied data")
        self._incoming_pending = False

    def _status(self) -> str:
        """Get the torrent status"""
        code = self._fields["status"].value
        if self._rpc_version() >= 14:
            return get_status_new(code)
        return get_status_old(code)

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
            files = self._fields["files"].value
            indices = range(len(files))
            priorities = self._fields["priorities"].value
            wanted = self._fields["wanted"].value
            for item in zip(indices, files, priorities, wanted):
                selected = bool(item[3])
                priority = PRIORITY[item[2]]
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
    def rateDownload(self) -> int:
        """
        Returns download rate in B/s

        :rtype: int
        """
        return self._fields["rateDownload"].value

    @property
    def rateUpload(self) -> int:
        """
        Returns upload rate in B/s

        :rtype: int
        """
        return self._fields["rateUpload"].value

    @property
    def hashString(self) -> str:
        """Returns the info hash of this torrent.

        :raise: AttributeError -- if server don't return this field
        :rtype: int
        """
        return self.__getattr__("hashString")

    @property
    def progress(self) -> float:
        """
        download progress in percent.

        :rtype: float
        """
        try:
            # https://gist.github.com/jackiekazil/6201722#gistcomment-2788556
            return round((100.0 * self._fields["percentDone"].value), 2)
        except KeyError:
            try:
                size = self._fields["sizeWhenDone"].value
                left = self._fields["leftUntilDone"].value
                return round((100.0 * (size - left) / float(size)), 2)
            except ZeroDivisionError:
                return 0.0

    @property
    def ratio(self) -> float:
        """
        upload/download ratio.

        :rtype: float
        """
        return float(self._fields["uploadRatio"].value)

    @property
    def eta(self) -> datetime.timedelta:
        """
        the "eta" as datetime.timedelta.

        :rtype: datetime.timedelta
        """
        eta = self._fields["eta"].value
        if eta >= 0:
            return datetime.timedelta(seconds=eta)
        raise ValueError("eta not valid")

    @property
    def date_active(self) -> datetime.datetime:
        """the attribute ``activityDate`` as ``datetime.datetime`` in **UTC timezone**.

        .. note::

            raw ``activityDate`` value could be ``0`` for never activated torrent,
            therefore it can't always be converted to local timezone.


        :rtype: datetime.datetime
        """
        return datetime.datetime.fromtimestamp(
            self._fields["activityDate"].value, datetime.timezone.utc
        )

    @property
    def date_added(self) -> datetime.datetime:
        """raw field ``addedDate`` as ``datetime.datetime`` in **local timezone**.

        :rtype: datetime.datetime
        """
        return datetime.datetime.fromtimestamp(
            self._fields["addedDate"].value
        ).astimezone()

    @property
    def date_started(self) -> datetime.datetime:
        """raw field ``startDate`` as ``datetime.datetime`` in **local timezone**.

        :rtype: datetime.datetime
        """
        return datetime.datetime.fromtimestamp(
            self._fields["startDate"].value
        ).astimezone()

    @property
    def date_done(self) -> Optional[datetime.datetime]:
        """the attribute "doneDate" as datetime.datetime. returns None if "doneDate" is invalid."""
        done_date = self._fields["doneDate"].value
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
        eta = self._fields["eta"].value
        if eta == -1:
            return "not available"
        if eta == -2:
            return "unknown"
        return format_timedelta(self.eta)

    @property
    def download_dir(self) -> Optional[str]:
        """The download directory.

        :available: transmission version 1.5.
        :available: RPC version 4.
        """
        return self._fields["downloadDir"].value

    @property
    def download_limit(self) -> Optional[int]:
        """The download limit.

        Can be a number or None.
        """
        if self._fields["downloadLimited"].value:
            return self._fields["downloadLimit"].value
        return None

    @download_limit.setter
    def download_limit(self, limit: int) -> None:
        """Download limit in Kbps or None."""
        if isinstance(limit, int):
            self._fields["downloadLimited"] = Field(True, True)
            self._fields["downloadLimit"] = Field(limit, True)
            self._push()
        elif limit is None:
            self._fields["downloadLimited"] = Field(False, True)
            self._push()
        else:
            raise ValueError("Not a valid limit")

    @property
    def peer_limit(self) -> int:
        """the peer limit."""
        return self._fields["peer_limit"].value

    @peer_limit.setter
    def peer_limit(self, limit: int) -> None:
        """
        Set the peer limit.
        """
        if isinstance(limit, int):
            self._fields["peer_limit"] = Field(limit, True)
            self._push()
        else:
            raise ValueError("Not a valid limit")

    @property
    def priority(self) -> str:
        """
        Bandwidth priority as string.
        Can be one of 'low', 'normal', 'high'. This is a mutator.
        """

        return PRIORITY[self._fields["bandwidthPriority"].value]

    @priority.setter
    def priority(self, priority: str) -> None:
        if isinstance(priority, str):
            self._fields["bandwidthPriority"] = Field(PRIORITY[priority], True)
            self._push()

    @property
    def seed_idle_limit(self) -> int:
        """
        seed idle limit in minutes.
        """
        return self._fields["seedIdleLimit"].value

    @seed_idle_limit.setter
    def seed_idle_limit(self, limit: int) -> None:
        """
        Set the seed idle limit in minutes.
        """
        if isinstance(limit, int):
            self._fields["seedIdleLimit"] = Field(limit, True)
            self._push()
        else:
            raise ValueError("Not a valid limit")

    @property
    def is_finished(self) -> bool:
        """Returns true if the torrent is finished (available from rpc version 2.0)"""
        return self._fields["isFinished"].value

    @property
    def is_stalled(self) -> bool:
        """Returns true if the torrent is stalled (available from rpc version 2.4)"""
        return self._fields["isStalled"].value

    @property
    def size_when_done(self) -> int:
        """Size in bytes when the torrent is done"""
        return self._fields["sizeWhenDone"].value

    @property
    def total_size(self) -> int:
        """Total size in bytes"""
        return self._fields["totalSize"].value

    @property
    def left_until_done(self) -> int:
        """Bytes left until done"""
        return self._fields["leftUntilDone"].value

    @property
    def desired_available(self) -> int:
        """Bytes that are left to download and available"""
        return self._fields["desiredAvailable"].value

    @property
    def available(self) -> float:
        """Availability in percent"""
        bytes_all = self.total_size
        bytes_done = sum(
            map(lambda x: x["bytesCompleted"], self._fields["fileStats"].value)
        )
        bytes_avail = self.desired_available + bytes_done
        return (bytes_avail / bytes_all) * 100 if bytes_all else 0

    @property
    def seed_idle_mode(self) -> str:
        """
        Seed idle mode as string. Can be one of 'global', 'single' or 'unlimited'.

         * global, use session seed idle limit.
         * single, use torrent seed idle limit. See seed_idle_limit.
         * unlimited, no seed idle limit.
        """
        return IDLE_LIMIT[self._fields["seedIdleMode"].value]

    @seed_idle_mode.setter
    def seed_idle_mode(self, mode: Union[str, int]) -> None:
        """
        Set the seed ratio mode.
        Can be one of ``global``, ``single`` or ``unlimited``, or ``0``, ``1``, ``2``.
        """
        if isinstance(mode, str):
            self._fields["seedIdleMode"] = Field(IDLE_LIMIT[mode], True)
            self._push()
        elif isinstance(mode, int):
            self._fields["seedIdleMode"] = Field(IDLE_LIMIT[mode], True)
            self._push()
        else:
            raise ValueError("Not a valid limit")

    @property
    def seed_ratio_limit(self) -> float:
        """
        Torrent seed ratio limit as float. Also see seed_ratio_mode.
        This is a mutator.

        :rtype: float
        """

        return float(self._fields["seedRatioLimit"].value)

    @seed_ratio_limit.setter
    def seed_ratio_limit(self, limit: Union[int, float]) -> None:
        """
        Set the seed ratio limit as float.
        """
        if isinstance(limit, (int, float)) and limit >= 0.0:
            self._fields["seedRatioLimit"] = Field(float(limit), True)
            self._push()
        else:
            raise ValueError("Not a valid limit")

    @property
    def seed_ratio_mode(self) -> str:
        """
        Seed ratio mode as string. Can be one of 'global', 'single' or 'unlimited'.

         * global, use session seed ratio limit.
         * single, use torrent seed ratio limit. See seed_ratio_limit.
         * unlimited, no seed ratio limit.

        This is a mutator.
        """
        return RATIO_LIMIT[self._fields["seedRatioMode"].value]

    @seed_ratio_mode.setter
    def seed_ratio_mode(self, mode: Union[str, int]) -> None:
        """
        Set the seed ratio mode.
        Can be one of ``'global'``, ``'single'`` or ``'unlimited'``, or ``0``, ``1``, ``2``.
        """
        if isinstance(mode, str):
            self._fields["seedRatioMode"] = Field(RATIO_LIMIT[mode], True)
            self._push()
        elif isinstance(mode, int):
            self._fields["seedRatioMode"] = Field(mode, True)
            self._push()
        else:
            raise ValueError("Not a valid limit")

    @property
    def upload_limit(self) -> Optional[int]:
        """
        upload limit.
        Can be a number or None.
        """
        if self._fields["uploadLimited"].value:
            return self._fields["uploadLimit"].value
        return None

    @upload_limit.setter
    def upload_limit(self, limit: Optional[int]) -> None:
        """Upload limit in Kbps or None."""
        if isinstance(limit, int):
            self._fields["uploadLimited"] = Field(True, True)
            self._fields["uploadLimit"] = Field(limit, True)
            self._push()
        elif limit is None:
            self._fields["uploadLimited"] = Field(False, True)
            self._push()
        else:
            raise ValueError("Not a valid limit")

    @property
    def queue_position(self) -> int:
        """queue position for this torrent."""
        if self._rpc_version() >= 14:
            return self._fields["queuePosition"].value
        return 0

    @queue_position.setter
    def queue_position(self, position: str) -> None:
        """Queue position"""
        if self._rpc_version() >= 14:
            if isinstance(position, int):
                self._fields["queuePosition"] = Field(position, True)
                self._push()
            else:
                raise ValueError("Not a valid position")
        else:
            pass

    def update(self, timeout: _Timeout = None) -> None:
        """Update the torrent information."""
        self._push()
        torrent = self._client.get_torrent(self.id, timeout=timeout)
        self._update_fields(torrent)

    def start(self, bypass_queue: bool = False, timeout: _Timeout = None) -> None:
        """
        Start the torrent.
        """
        self._incoming_pending = True
        self._client.start_torrent(self.id, bypass_queue=bypass_queue, timeout=timeout)

    def stop(self, timeout: _Timeout = None) -> None:
        """Stop the torrent."""
        self._incoming_pending = True
        self._client.stop_torrent(self.id, timeout=timeout)

    def move_data(self, location: str, timeout: _Timeout = None) -> None:
        """Move torrent data to location."""
        self._incoming_pending = True
        self._client.move_torrent_data(self.id, location, timeout=timeout)

    def locate_data(self, location: str, timeout: _Timeout = None) -> None:
        """Locate torrent data at location."""
        self._incoming_pending = True
        self._client.locate_torrent_data(self.id, location, timeout=timeout)
