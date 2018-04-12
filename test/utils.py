# -*- coding: utf-8 -*-
# 2008-12, Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.

import datetime
import unittest
import transmission_rpc.utils as tu

from six import iteritems

class utils(unittest.TestCase):
    def testFormatSize(self):
        table = {
            512: (512, 'B'),
            1024: (1.0, 'KiB'),
            1048575: (1023.999, 'KiB'),
            1048576: (1.0, 'MiB'),
            1073741824: (1.0, 'GiB'),
            1099511627776: (1.0, 'TiB'),
            1125899906842624: (1.0, 'PiB'),
            1152921504606846976: (1.0, 'EiB'),
        }
        for size, expected in iteritems(table):
            result = tu.format_size(size)
            self.assertAlmostEqual(result[0], expected[0], 4)
            self.assertEqual(result[1], expected[1])

    def testFormatSpeed(self):
        table = {
            512: (512, 'B/s'),
            1024: (1.0, 'KiB/s'),
            1048575: (1023.999, 'KiB/s'),
            1048576: (1.0, 'MiB/s'),
            1073741824: (1.0, 'GiB/s'),
            1099511627776: (1.0, 'TiB/s'),
            1125899906842624: (1.0, 'PiB/s'),
            1152921504606846976: (1.0, 'EiB/s'),
        }
        for size, expected in iteritems(table):
            result = tu.format_speed(size)
            self.assertAlmostEqual(result[0], expected[0], 4)
            self.assertEqual(result[1], expected[1])

    def testFormatTimedelta(self):
        table = {
            datetime.timedelta(0, 0): '0 00:00:00',
            datetime.timedelta(0, 10): '0 00:00:10',
            datetime.timedelta(0, 60): '0 00:01:00',
            datetime.timedelta(0, 61): '0 00:01:01',
            datetime.timedelta(0, 3661): '0 01:01:01',
            datetime.timedelta(1, 3661): '1 01:01:01',
            datetime.timedelta(13, 65660): '13 18:14:20',
        }
        for delta, expected in iteritems(table):
            self.assertEqual(tu.format_timedelta(delta), expected)

    def testFormatTimestamp(self):
        table = {
            0: '-',
            1: '1970-01-01 00:00:01',
            1129135532: '2005-10-12 16:45:32',
        }
        for timestamp, expected in iteritems(table):
            self.assertEqual(tu.format_timestamp(timestamp, utc=True), expected)

    def testInetAddress(self):
        table = {
            ('127.0.0.1:80', 2000): ('127.0.0.1', 80),
            ('127.0.0.1', 2000): ('127.0.0.1', 2000),
            (':80', 2000): ('localhost', 80),
            (':80', 2000, '127.0.0.1'): ('127.0.0.1', 80),
            ('0.0.0.0:443', 2000): ('0.0.0.0', 443),
             ('localhost:443', 2000): ('localhost', 443),
        }
        for args, expected in iteritems(table):
            self.assertEqual(tu.inet_address(*args), expected)

        self.assertRaises(tu.INetAddressError, tu.inet_address, '256.256.256.256', 2000)

    def testRPCBool(self):
        table = {
            0: 0,
            1: 1,
            1000: 1,
            'true': 1,
            'Yes': 1,
            'truE': 1,
            'baka': 0,
            'false': 0,
            'no': 0,
            True: 1,
            False: 0,
        }
        for value, expected in iteritems(table):
            self.assertEqual(tu.rpc_bool(value), expected)

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(utils)
    return suite

if __name__ == '__main__':
    unittest.main()
