import pytest

from transmission_rpc.error import ServerVersionTooLow
from transmission_rpc.client import Client
from transmission_rpc.decorator import arg


class C(Client):
    def _request(
        self,
        method,
        arguments=None,
        ids=None,
        require_ids=False,
        timeout=None
    ):
        pass

    @property
    def rpc_version(self):
        return 10

    @arg('high', 11)
    @arg('equal', 10)
    @arg('lower', 9)
    def t(self, **kwargs):
        return kwargs


def test_kwarg_require_rpc_version():
    c = C()
    assert c.t(lower=1) == {'lower': 1}

    assert c.t(equal=1) == {'equal': 1}

    with pytest.raises(ServerVersionTooLow):
        c.t(high=1)
