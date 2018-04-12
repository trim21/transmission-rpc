# -*- coding: utf-8 -*-
# 2008-12, Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.

import unittest
from . import top, client, torrent, utils

def test():
    tests = unittest.TestSuite([top.suite(), utils.suite(), torrent.suite(), client.suite()])
    result = unittest.TestResult()
    tests.run(result, True)
    for e in result.errors:
        for m in e:
            print(m)

test()
