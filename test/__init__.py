# 2008-12, Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.

import unittest

from tests import test_utils

from . import torrent


def test():
    tests = unittest.TestSuite([
        test_utils.suite(),
        torrent.suite(),
    ])
    result = unittest.TestResult()
    tests.run(result, True)
    for e in result.errors:
        for m in e:
            print(m)


test()
