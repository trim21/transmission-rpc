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

__author__    		= 'Trim21 <trim21me@hotmail.com>'
__version__   		= '0.0.3'
__author_email__ 	= 'trim21me@hotmail.com'
__copyright__ 		= 'Copyright (c) 2018 Trim21'
__license__   		= 'MIT'
