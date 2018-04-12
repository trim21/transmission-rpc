# -*- coding: utf-8 -*-
# 2013-03, Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.

import unittest
import transmission_rpc

class TopTest(unittest.TestCase):

    def testConstants(self):
        self.assertTrue(isinstance(transmission_rpc.__author__, str))
        self.assertTrue(isinstance(transmission_rpc.__version_major__, int))
        self.assertTrue(isinstance(transmission_rpc.__version_minor__, int))
        self.assertTrue(isinstance(transmission_rpc.__version__, str))
        self.assertTrue(isinstance(transmission_rpc.__copyright__, str))
        self.assertTrue(isinstance(transmission_rpc.__license__, str))

        self.assertEqual('{0}.{1}'.format(transmission_rpc.__version_major__, transmission_rpc.__version_minor__), transmission_rpc.__version__)

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TopTest)
    return suite
