#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 Trim21 <trim21me@hotmail.com>
# Licensed under the MIT license.

from setuptools import setup

setup(
    use_scm_version={
        "write_to": "transmission_rpc/version.py",
        "write_to_template": 'version = {version!r}',
    },
    test_suite="test",
)
