#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 Trim21 <trim21me@hotmail.com>
# Licensed under the MIT license.
import os
import os.path
import re
from setuptools import setup


def _get_version():
    PATH_TO_INIT_PY = \
        os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'transmission_rpc',
            '__init__.py'
        )

    with open(PATH_TO_INIT_PY, 'r', encoding='utf-8') as fp:
        try:
            for line in fp.readlines():
                if line:
                    line = line.strip()
                    _version = re.findall(r"^__version__ = '([^']+)'$", line,
                                          re.M)
                    if _version:
                        return _version[0]
        except IndexError:
            raise RuntimeError('Unable to determine version.')


os.environ['PBR_VERSION'] = _get_version()

setup(
    pbr=True,
)
