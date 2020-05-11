# 2008-12, Erik Svensson <erik.public@gmail.com>
# Copyright (c) 2018-2020 Trim21 <i@trim21.me>
# Licensed under the MIT license.
import datetime
import unittest

from transmission_rpc import utils


class TestUtils(unittest.TestCase):
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
        for size, expected in table.items():
            result = utils.format_size(size)
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
        for size, expected in table.items():
            result = utils.format_speed(size)
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
        for delta, expected in table.items():
            self.assertEqual(utils.format_timedelta(delta), expected)

    def testFormatTimestamp(self):
        table = {
            0: '-',
            1: '1970-01-01 00:00:01',
            1129135532: '2005-10-12 16:45:32',
        }
        for timestamp, expected in table.items():
            self.assertEqual(utils.format_timestamp(timestamp, utc=True), expected)

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
        for value, expected in table.items():
            self.assertEqual(utils.rpc_bool(value), expected)
