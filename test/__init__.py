# 2008-12, Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.

import unittest

from . import top, utils, client, torrent


def test():
    tests = unittest.TestSuite([top.suite(), utils.suite(), torrent.suite(), client.suite()])
    result = unittest.TestResult()
    tests.run(result, True)
    for e in result.errors:
        for m in e:
            print(m)


test()
