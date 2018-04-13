#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 Trim21 <trim21me@hotmail.com>
# Licensed under the MIT license.

from setuptools import setup
from transmission_rpc import __version__, __author__, __author_email__

required = ['six>=1.1.0']


def long_description():
    with open('./README.md', 'rb') as f:
        return f.read().decode('utf-8')
setup(
    name='transmission_rpc',
    version=__version__,
    description='Python module that implements the Transmission bittorent client RPC protocol.',
    author=__author__,
    author_email=__author_email__,
    url='https://github.com/Trim21/transmission-rpc',
    keywords='transmission rpc',
    packages=['transmission_rpc'],
    install_requires = required,
    long_description=long_description(),
    test_suite = "test",
    zip_safe=True,
    classifiers = [
        'Intended Audience :: Developers',
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Topic :: Communications :: File Sharing',
        'Topic :: Internet',
        'Topic :: Software Development :: Version Control :: Git',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        ],
    )
