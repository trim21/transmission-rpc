# -*- coding: utf-8 -*-
# 2008-12, Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.

import os
import unittest
import base64

from six import iteritems, string_types, PY3

if PY3:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse

import json
import transmissionrpc.constants
from transmissionrpc import TransmissionError, Client, HTTPHandler

def tree_differences(a, b):
    return node_differences(a, b, '.')

def node_differences(a, b, root):
    errors = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k, v in iteritems(a):
            node = root + '.' + k
            if k not in b:
                errors.append('Field %s missing from b at %s' % (k, node))
            else:
                errors.extend(node_differences(a[k], b[k], node))
        for k, v in iteritems(b):
            node = root + '.' + k
            if k not in a:
                errors.append('Field %s missing from a at %s' % (k, node))
    elif isinstance(a, list) and isinstance(b, list):
        for v in a:
            if v not in b:
                errors.append('Value %s missing from b at %s' % (v[0:32], root))
        for v in b:
            if v not in a:
                errors.append('Value %s missing from a at %s' % (v[0:32], root))
    else:
        if a != b:
            errors.append('Value %s != %s at %s' % (a[0:32], b[0:32], root))
    return errors

class TestHTTPHandler(HTTPHandler):
    def __init__(self, test_name=None):
        self.url = None
        self.user = None
        self.password = None
        self.tests = None
        self.test_index = 0
        if test_name:
            test_file = test_name + '.json'
            here = os.path.dirname(os.path.abspath(__file__))
            test_path = os.path.join(here, 'data', test_file)
            fd = open(test_path, 'r')
            test_data = json.load(fd)
            fd.close()
            if 'test sequence' in test_data:
                self.tests = test_data['test sequence']
    
    def set_authentication(self, url, user, password):
        urlo = urlparse(url)
        if urlo.scheme == '':
            raise ValueError('URL should have a scheme.')
        else:
            self.url = url
        if user and password:
            if isinstance(user, string_types):
                self.user = user
            else:
                raise TypeError('Invalid type for user.')
            if isinstance(password, string_types):
                self.password = password
            else:
                raise TypeError('Invalid type for password.')
        elif user or password:
            raise ValueError('User AND password or neither.')
    
    def request(self, url, query, headers, timeout):
        response = {}
        if self.url and self.url != url:
            raise ValueError('New URL?!')
        urlo = urlparse(url)
        if urlo.scheme == '':
            raise ValueError('URL should have a scheme.')
        else:
            self.url = url
        q = json.loads(query)
        
        if self.tests:
            test_data = self.tests[self.test_index]
            self.test_index += 1
            errors = tree_differences(test_data['request'], q)
            if len(errors) > 0:
                errors = '\n\t'.join(errors)
                raise Exception('Invalid request\n%s\n%s\n. Errors: %s\n' % (json.dumps(q, indent=2), json.dumps(test_data['request'], indent=2), errors))
            if 'response' in test_data:
                response = test_data['response']
        else:
            response['tag'] = int(q['tag'])
            response['result'] = 'success'
        return json.dumps(response)

def createClient(*args, **kwargs):
    test_name = None
    if 'test_name' in kwargs:
        test_name = kwargs['test_name']
        del kwargs['test_name']
    kwargs['http_handler'] = TestHTTPHandler(test_name)
    return Client(*args, **kwargs)

class ClientTest(unittest.TestCase):

    def testConstruction(self):
        tc = createClient(test_name='construction')
        self.assertEqual(tc.url, 'http://localhost:%d/transmission/rpc' % (transmissionrpc.constants.DEFAULT_PORT))
        tc = createClient('127.0.0.1', 7000, user='user', password='secret', test_name='construction')
        self.assertEqual(tc.url, 'http://127.0.0.1:7000/transmission/rpc')
        tc = createClient('127.0.0.1', 7000, user='user', password='secret', test_name='construction')
        self.assertEqual(tc.url, 'http://127.0.0.1:7000/transmission/rpc')
        tc = createClient('127.0.0.1', 7000, user='user', test_name='construction')
        self.assertEqual(tc.url, 'http://127.0.0.1:7000/transmission/rpc')
        tc = createClient('127.0.0.1', 7000, password='secret', test_name='construction')
        self.assertEqual(tc.url, 'http://127.0.0.1:7000/transmission/rpc')
        tc = createClient('127.0.0.1', 7000, password='secret', timeout=0.1, test_name='construction')
        self.assertEqual(tc.url, 'http://127.0.0.1:7000/transmission/rpc')
        self.assertEqual(tc.timeout, 0.1)
        tc = createClient('127.0.0.1', 7000, password='secret', timeout=10, test_name='construction')
        self.assertEqual(tc.timeout, 10.0)
        tc = createClient('127.0.0.1', 7000, password='secret', timeout=10, test_name='construction')
        self.assertEqual(tc.timeout, 10.0)

    def testTimeoutProperty(self):
        tc = createClient('127.0.0.1', 12345, timeout=10, test_name='construction')
        self.assertEqual(tc.timeout, 10.0)
        tc.timeout = 0.1
        self.assertEqual(tc.timeout, 0.1)
        tc.timeout = 100
        self.assertEqual(tc.timeout, 100.0)
        tc.timeout = 100
        self.assertEqual(tc.timeout, 100.0)
        del tc.timeout
        self.assertEqual(tc.timeout, transmissionrpc.constants.DEFAULT_TIMEOUT)
        tc.timeout = '100.1'
        self.assertEqual(tc.timeout, 100.1)
        self.failUnlessRaises(ValueError, tc._set_timeout, '10 years')
            
    def testAddOld(self):
        tc = createClient(test_name='add')
        data = 'data'
        
        r = tc.add(data)[0]
        self.assertEqual(r.id, 0)
        self.assertEqual(r.hashString, 'A000')
        self.assertEqual(r.name, 'testtransfer0')
        
        r = tc.add(data, paused=True)[1]
        self.assertEqual(r.id, 1)
        self.assertEqual(r.hashString, 'A001')
        self.assertEqual(r.name, 'testtransfer1')
        
        r = tc.add(data, download_dir='/tmp')[2]
        self.assertEqual(r.id, 2)
        self.assertEqual(r.hashString, 'A002')
        self.assertEqual(r.name, 'testtransfer2')
        
        r = tc.add(data, peer_limit=10)[3]
        self.assertEqual(r.id, 3)
        self.assertEqual(r.hashString, 'A003')
        self.assertEqual(r.name, 'testtransfer3')
        
        r = tc.add(data, paused=True, download_dir='/tmp', peer_limit=10)[4]
        self.assertEqual(r.id, 4)
        self.assertEqual(r.hashString, 'A004')
        self.assertEqual(r.name, 'testtransfer4')
        
        self.failUnlessRaises(ValueError, tc.add, data, peer_limit='apa')

    def testAddUriOld(self):
        data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        tc = createClient(test_name='adduri')

        r = tc.add_uri('torrent.txt', paused=False, download_dir='/var/downloads', peer_limit=1)[0]
        self.assertEqual(r.id, 0)
        self.assertEqual(r.hashString, 'A000')
        self.assertEqual(r.name, 'testtransfer0')

        r = tc.add_uri('file://' + os.path.join(data_path, 'torrent.txt'), paused=True, download_dir='/tmp', peer_limit=200)[1]
        self.assertEqual(r.id, 1)
        self.assertEqual(r.hashString, 'A001')
        self.assertEqual(r.name, 'testtransfer1')

    def testAddTorrent(self):
        data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

        tc = createClient(test_name='add_torrent_base64')
        torrent_path = os.path.join(data_path, 'ubuntu-12.04.2-alternate-amd64.iso.torrent')
        data = open(torrent_path, 'rb').read()
        data_b64 = base64.b64encode(data).decode('utf-8')
        r = tc.add_torrent(data_b64)
        self.assertEqual(r.id, 0)
        self.assertEqual(r.hashString, 'a21c45469c565f3fb9595e4e9707e6e9d45abca6')
        self.assertEqual(r.name, 'ubuntu-12.04.2-alternate-amd64.iso')

        tc = createClient(test_name='adduri')
        self.assertRaises(ValueError, tc.add_torrent, None)

        r = tc.add_torrent('torrent.txt', paused=False, download_dir='/var/downloads', peer_limit=1)
        self.assertEqual(r.id, 0)
        self.assertEqual(r.hashString, 'A000')
        self.assertEqual(r.name, 'testtransfer0')

        r = tc.add_torrent('file://' + os.path.join(data_path, 'torrent.txt'), paused=True, download_dir='/tmp', peer_limit=200)
        self.assertEqual(r.id, 1)
        self.assertEqual(r.hashString, 'A001')
        self.assertEqual(r.name, 'testtransfer1')

    def testRemoveOld(self):
        tc = createClient(test_name='remove')
        
        tc.remove(['b000', 2, 3])
        tc.remove(1, delete_data=True)
        tc.remove('b002', delete_data=False)

    def testRemoveTorrent(self):
        tc = createClient(test_name='remove')
        
        tc.remove_torrent(['b000', 2, 3])
        tc.remove_torrent(1, delete_data=True)
        tc.remove_torrent('b002', delete_data=False)

    def testStartOld(self):
        tc = createClient(test_name='start')
        
        tc.start(['abcdef', 20, 30])
        tc.start(1)
        tc.start('a0123456789')

    def testStartTorrent(self):
        tc = createClient(test_name='start')
        
        tc.start_torrent(['abcdef', 20, 30])
        tc.start_torrent(1)
        tc.start_torrent('a0123456789')

    def testStopOld(self):
        tc = createClient(test_name='stop')
        
        tc.stop(2)
        tc.stop('bad')
        tc.stop(['bad', 'ba5', '30', 20])

    def testStopTorrent(self):
        tc = createClient(test_name='stop')
        
        tc.stop(2)
        tc.stop('bad')
        tc.stop(['bad', 'ba5', '30', 20])

    def testVerifyOld(self):
        tc = createClient(test_name='verify')
        
        tc.verify(10000)
        tc.verify('d')
        tc.verify(['a', 'b', 'c'])

    def testVerifyTorrent(self):
        tc = createClient(test_name='verify')
        
        tc.verify_torrent(10000)
        tc.verify_torrent('d')
        tc.verify_torrent(['a', 'b', 'c'])

    def testInfo(self):
        tc = createClient(test_name='info')
        
        r = tc.info()
        self.assertTrue(2 in r)
        self.assertTrue(3 in r)
        t = r[2]
        self.assertEqual(t.id, 2)
        self.assertEqual(t.name, 'ubuntu-10.04-server-amd64.iso')
        self.assertEqual(t.hashString, 'ab8ea951c022d4745a9b06ab8020b952a52b71ca')

    def testGetTorrent(self):
        tc = createClient(test_name='get_torrent')
        torrent = tc.get_torrent(2)
        self.assertEqual(torrent.id, 2)
        self.assertEqual(torrent.name, 'ubuntu-10.04-server-amd64.iso')
        self.assertEqual(torrent.hashString, 'ab8ea951c022d4745a9b06ab8020b952a52b71ca')

        tc = createClient(test_name='get_torrent_hash')
        torrent = tc.get_torrent('ab8ea951c022d4745a9b06ab8020b952a52b71ca')
        self.assertEqual(torrent.id, 2)
        self.assertEqual(torrent.name, 'ubuntu-10.04-server-amd64.iso')
        self.assertEqual(torrent.hashString, 'ab8ea951c022d4745a9b06ab8020b952a52b71ca')

    def testGetTorrents(self):
        tc = createClient(test_name='info')
        r = tc.get_torrents()
        for torrent in r:
            if torrent.id == 2:
                self.assertEqual(torrent.name, 'ubuntu-10.04-server-amd64.iso')
                self.assertEqual(torrent.hashString, 'ab8ea951c022d4745a9b06ab8020b952a52b71ca')
            elif torrent.id == 3:
                self.assertEqual(torrent.name, 'ubuntu-10.04-alternate-i386.iso')
                self.assertEqual(torrent.hashString, 'a33e98826003515e46ef5075fcbf4914b307abe2')
            else:
                self.fail("Unknown torrent")

    def testGetTorrentsRange(self):
        tc = createClient(test_name='get_torrents_2to3')        
        r = tc.get_torrents([2,3])
        for torrent in r:
            if torrent.id == 2:
                self.assertEqual(torrent.name, 'ubuntu-10.04-server-amd64.iso')
                self.assertEqual(torrent.hashString, 'ab8ea951c022d4745a9b06ab8020b952a52b71ca')
            elif torrent.id == 3:
                self.assertEqual(torrent.name, 'ubuntu-10.04-alternate-i386.iso')
                self.assertEqual(torrent.hashString, 'a33e98826003515e46ef5075fcbf4914b307abe2')
            else:
                self.fail("Unknown torrent")
        
        tc = createClient(test_name='get_torrents_2to3')        
        r = tc.get_torrents("2:3")
        for torrent in r:
            if torrent.id == 2:
                self.assertEqual(torrent.name, 'ubuntu-10.04-server-amd64.iso')
                self.assertEqual(torrent.hashString, 'ab8ea951c022d4745a9b06ab8020b952a52b71ca')
            elif torrent.id == 3:
                self.assertEqual(torrent.name, 'ubuntu-10.04-alternate-i386.iso')
                self.assertEqual(torrent.hashString, 'a33e98826003515e46ef5075fcbf4914b307abe2')
            else:
                self.fail("Unknown torrent")
        
        tc = createClient(test_name='get_torrents_2to3')
        r = tc.get_torrents("2,3")
        for torrent in r:
            if torrent.id == 2:
                self.assertEqual(torrent.name, 'ubuntu-10.04-server-amd64.iso')
                self.assertEqual(torrent.hashString, 'ab8ea951c022d4745a9b06ab8020b952a52b71ca')
            elif torrent.id == 3:
                self.assertEqual(torrent.name, 'ubuntu-10.04-alternate-i386.iso')
                self.assertEqual(torrent.hashString, 'a33e98826003515e46ef5075fcbf4914b307abe2')
            else:
                self.fail("Unknown torrent")
        
        tc = createClient(test_name='get_torrents_2to3')
        r = tc.get_torrents("2 3")
        for torrent in r:
            if torrent.id == 2:
                self.assertEqual(torrent.name, 'ubuntu-10.04-server-amd64.iso')
                self.assertEqual(torrent.hashString, 'ab8ea951c022d4745a9b06ab8020b952a52b71ca')
            elif torrent.id == 3:
                self.assertEqual(torrent.name, 'ubuntu-10.04-alternate-i386.iso')
                self.assertEqual(torrent.hashString, 'a33e98826003515e46ef5075fcbf4914b307abe2')
            else:
                self.fail("Unknown torrent")
        
    def testGetTorrentsHashes(self):
        tc = createClient(test_name='get_torrents_hashes')        
        r = tc.get_torrents(["ab8ea951c022d4745a9b06ab8020b952a52b71ca", "a33e98826003515e46ef5075fcbf4914b307abe2"])
        for torrent in r:
            if torrent.id == 2:
                self.assertEqual(torrent.name, 'ubuntu-10.04-server-amd64.iso')
                self.assertEqual(torrent.hashString, 'ab8ea951c022d4745a9b06ab8020b952a52b71ca')
            elif torrent.id == 3:
                self.assertEqual(torrent.name, 'ubuntu-10.04-alternate-i386.iso')
                self.assertEqual(torrent.hashString, 'a33e98826003515e46ef5075fcbf4914b307abe2')
            else:
                self.fail("Unknown torrent")
        
        tc = createClient(test_name='get_torrents_hashes')        
        r = tc.get_torrents("ab8ea951c022d4745a9b06ab8020b952a52b71ca,a33e98826003515e46ef5075fcbf4914b307abe2")
        for torrent in r:
            if torrent.id == 2:
                self.assertEqual(torrent.name, 'ubuntu-10.04-server-amd64.iso')
                self.assertEqual(torrent.hashString, 'ab8ea951c022d4745a9b06ab8020b952a52b71ca')
            elif torrent.id == 3:
                self.assertEqual(torrent.name, 'ubuntu-10.04-alternate-i386.iso')
                self.assertEqual(torrent.hashString, 'a33e98826003515e46ef5075fcbf4914b307abe2')
            else:
                self.fail("Unknown torrent")

        tc = createClient(test_name='get_torrents_hashes')        
        r = tc.get_torrents("ab8ea951c022d4745a9b06ab8020b952a52b71ca a33e98826003515e46ef5075fcbf4914b307abe2")
        for torrent in r:
            if torrent.id == 2:
                self.assertEqual(torrent.name, 'ubuntu-10.04-server-amd64.iso')
                self.assertEqual(torrent.hashString, 'ab8ea951c022d4745a9b06ab8020b952a52b71ca')
            elif torrent.id == 3:
                self.assertEqual(torrent.name, 'ubuntu-10.04-alternate-i386.iso')
                self.assertEqual(torrent.hashString, 'a33e98826003515e46ef5075fcbf4914b307abe2')
            else:
                self.fail("Unknown torrent")

    def testParseId(self):
        from transmissionrpc.client import parse_torrent_id
        self.assertEqual(parse_torrent_id(None), None)
        self.assertEqual(parse_torrent_id(10), 10)
        self.assertEqual(parse_torrent_id(10.0), 10)
        self.assertEqual(parse_torrent_id(10.5), None)
        self.assertEqual(parse_torrent_id("10"), 10)
        self.assertEqual(parse_torrent_id("A"), "A")
        self.assertEqual(parse_torrent_id("a21c45469c565f3fb9595e4e9707e6e9d45abca6"), "a21c45469c565f3fb9595e4e9707e6e9d45abca6")
        self.assertEqual(parse_torrent_id("T"), None)
        self.assertEqual(parse_torrent_id([10]), None)
        self.assertEqual(parse_torrent_id((10, 11)), None)
        self.assertEqual(parse_torrent_id({10: 10}), None)

    def testParseIds(self):
        from transmissionrpc.client import parse_torrent_ids
        self.assertEqual(parse_torrent_ids(None), [])
        self.assertEqual(parse_torrent_ids(10), [10])
        self.assertEqual(parse_torrent_ids(10.0), [10])
        self.assertEqual(parse_torrent_ids("10"), [10])
        self.assertEqual(parse_torrent_ids("A"), ["A"])
        self.assertEqual(parse_torrent_ids("a21c45469c565f3fb9595e4e9707e6e9d45abca6"), ["a21c45469c565f3fb9595e4e9707e6e9d45abca6"])
        self.assertEqual(parse_torrent_ids(",, "), [])
        self.assertEqual(parse_torrent_ids("1,2,3"), [1,2,3])
        self.assertEqual(parse_torrent_ids("1:3"), [1,2,3])
        self.assertRaises(ValueError, parse_torrent_ids, "A:3")
        self.assertRaises(ValueError, parse_torrent_ids, "T")
        self.assertEqual(parse_torrent_ids([10]), [10])
        self.assertEqual(parse_torrent_ids((10, 11)), [10, 11])
        self.assertRaises(ValueError, parse_torrent_ids, {10: 10})

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(ClientTest)
    return suite
