#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 Trim21 <trim21me@hotmail.com>
# Licensed under the MIT license.

import textwrap

from setuptools import setup


def long_description():
    with open('./README.md', 'rb') as f:
        return f.read().decode('utf-8')


setup(
    use_scm_version={
        "write_to": "transmission_rpc/__init__.py",
        "write_to_template": textwrap.dedent(
            """
             # coding: utf-8
             __version__ = {version!r}
             """
        ).lstrip(),
    },

    test_suite="test",
)
