# -*- coding: utf-8 -*-
# 2013-03, Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.

import unittest
import transmissionrpc

class TopTest(unittest.TestCase):

    def testConstants(self):
        self.assertTrue(isinstance(transmissionrpc.__author__, str))
        self.assertTrue(isinstance(transmissionrpc.__version_major__, int))
        self.assertTrue(isinstance(transmissionrpc.__version_minor__, int))
        self.assertTrue(isinstance(transmissionrpc.__version__, str))
        self.assertTrue(isinstance(transmissionrpc.__copyright__, str))
        self.assertTrue(isinstance(transmissionrpc.__license__, str))

        self.assertEqual('{0}.{1}'.format(transmissionrpc.__version_major__, transmissionrpc.__version_minor__), transmissionrpc.__version__)

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TopTest)
    return suite
