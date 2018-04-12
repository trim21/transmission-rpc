#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2008-2014 Erik Svensson <erik.public@gmail.com>
# Licensed under the MIT license.

from setuptools import setup

required = ['six>=1.1.0']

setup(
    name='transmission_rpc',
    version='0.0.1',
    description='Python module that implements the Transmission bittorent client RPC protocol.',
    author='Trim21',
    author_email='trim21me@hotmail.com',
    url='https://github.com/Trim21/transmission-rpc',
    keywords='transmission rpc',
    packages=['transmission_rpc'],
    install_requires = required,
    test_suite = "test",
    zip_safe=True,
    classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Communications :: File Sharing',
        'Topic :: Internet'
        ],
    )
