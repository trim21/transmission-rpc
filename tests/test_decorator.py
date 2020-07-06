import pytest

from transmission_rpc.error import ServerVersionTooLow
from transmission_rpc.client import Client
from transmission_rpc.decorator import ArgumentsReplacedWarning, kwarg, replaced_by


class C(Client):
    def _request(self, *_, **__):
        pass

    @property
    def rpc_version(self):
        return 10

    @kwarg('high', 11)
    @kwarg('equal', 10)
    @kwarg('lower', 9)
    def t(self, **kwargs):
        return kwargs

    @replaced_by('old', 'new', 5)
    def r(self, **kwargs):
        return kwargs


def test_kwarg_require_rpc_version():
    c = C()
    assert c.t(lower=1) == {'lower': 1}

    assert c.t(equal=1) == {'equal': 1}

    with pytest.raises(ServerVersionTooLow):
        c.t(high=1)


def test_kwargs_replace():
    c = C()

    with pytest.warns(ArgumentsReplacedWarning):
        c.r(old=1)
