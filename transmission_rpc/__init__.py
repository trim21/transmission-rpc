# -*- coding: utf-8 -*-
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.

from transmission_rpc.constants import DEFAULT_PORT, DEFAULT_TIMEOUT, PRIORITY, RATIO_LIMIT, LOGGER
from transmission_rpc.error import TransmissionError, HTTPHandlerError
from transmission_rpc.httphandler import HTTPHandler, DefaultHTTPHandler
from transmission_rpc.torrent import Torrent
from transmission_rpc.session import Session
from transmission_rpc.client import Client
from transmission_rpc.utils import add_stdout_logger, add_file_logger

__author__    		= 'Erik Svensson <erik.public@gmail.com>'
__version_major__   = 0
__version_minor__   = 12
__version__   		= '{0}.{1}'.format(__version_major__, __version_minor__)
__copyright__ 		= 'Copyright (c) 2008-2014 Erik Svensson'
__license__   		= 'MIT'
