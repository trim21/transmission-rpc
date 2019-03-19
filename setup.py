#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 Trim21 <trim21me@hotmail.com>
# Licensed under the MIT license.

from setuptools import setup

setup(
    use_scm_version={
        "write_to": "transmission_rpc/__init__.py",
        "write_to_template": '\n__version__ = {version!r}',
    },
    test_suite="test",
)
