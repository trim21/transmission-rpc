# -*- coding: utf-8 -*-
# 2008-12, Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.

import time, datetime
import unittest
import transmission_rpc
import transmission_rpc.constants
import transmission_rpc.utils

class torrent(unittest.TestCase):
    def assertPropertyException(self, exception, object, property):
        try:
            getattr(object, property)
        except exception:
            pass
        else:
            self.fail()

    def testConstruction(self):
        self.failUnlessRaises(ValueError, transmission_rpc.Torrent, None, {})
        torrent = transmission_rpc.Torrent(None, {'id': 42})

    def testAttributes(self):
        torrent = transmission_rpc.Torrent(None, {'id': 42})
        self.assertTrue(hasattr(torrent, 'id'))
        self.assertEqual(torrent.id, 42)
        self.assertPropertyException(KeyError, torrent, 'status')
        self.assertPropertyException(KeyError, torrent, 'progress')
        self.assertPropertyException(KeyError, torrent, 'ratio')
        self.assertPropertyException(KeyError, torrent, 'eta')
        self.assertPropertyException(KeyError, torrent, 'date_active')
        self.assertPropertyException(KeyError, torrent, 'date_added')
        self.assertPropertyException(KeyError, torrent, 'date_started')
        self.assertPropertyException(KeyError, torrent, 'date_done')

        self.failUnlessRaises(KeyError, torrent.format_eta)
        self.assertEqual(torrent.files(), {})

        data = {
            'id': 1,
            'status': 4,
            'sizeWhenDone': 1000,
            'leftUntilDone': 500,
            'uploadedEver': 1000,
            'downloadedEver': 2000,
            'uploadRatio': 0.5,
            'eta': 3600,
            'activityDate': time.mktime((2008,12,11,11,15,30,0,0,-1)),
            'addedDate': time.mktime((2008,12,11,8,5,10,0,0,-1)),
            'startDate': time.mktime((2008,12,11,9,10,5,0,0,-1)),
            'doneDate': time.mktime((2008,12,11,10,0,15,0,0,-1)),
        }

        torrent = transmission_rpc.Torrent(None, data)
        self.assertEqual(torrent.id, 1)
        self.assertEqual(torrent.leftUntilDone, 500)
        self.assertEqual(torrent.status, 'downloading')
        self.assertEqual(torrent.progress, 50.0)
        self.assertEqual(torrent.ratio, 0.5)
        self.assertEqual(torrent.eta, datetime.timedelta(seconds=3600))
        self.assertEqual(torrent.date_active, datetime.datetime(2008,12,11,11,15,30))
        self.assertEqual(torrent.date_added, datetime.datetime(2008,12,11,8,5,10))
        self.assertEqual(torrent.date_started, datetime.datetime(2008,12,11,9,10,5))
        self.assertEqual(torrent.date_done, datetime.datetime(2008,12,11,10,0,15))

        self.assertEqual(torrent.format_eta(), transmission_rpc.utils.format_timedelta(torrent.eta))

        torrent = transmission_rpc.Torrent(None, {'id': 42, 'eta': -1})
        self.assertPropertyException(ValueError, torrent, 'eta')

        data = {
            'id': 1,
            'status': 4,
            'sizeWhenDone': 1000,
            'leftUntilDone': 500,
            'uploadedEver': 1000,
            'downloadedEver': 2000,
            'uploadRatio': 0.5,
            'eta': 3600,
            'activityDate': time.mktime((2008,12,11,11,15,30,0,0,-1)),
            'addedDate': time.mktime((2008,12,11,8,5,10,0,0,-1)),
            'startDate': time.mktime((2008,12,11,9,10,5,0,0,-1)),
            'doneDate': 0,
        }

        torrent = transmission_rpc.Torrent(None, data)
        self.assertEqual(torrent.date_done, None)

    def testUnicode(self):
        torrent = transmission_rpc.Torrent(None, {'id': 42, 'name': 'あみ'})
        self.assertEqual(torrent.id, 42)
        repr(torrent)
        str(torrent)

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(torrent)
    return suite
