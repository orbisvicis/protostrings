#!/usr/bin/env python


from setuptools import setup
from protostrings_metadata import metadata


setup\
    ( python_requires   = ">= 3"
    , install_requires  = [ "decorator" ]
    , setup_requires    = [ "pytest-runner", "setuptools >= 24.2.1" ]
    , tests_require     = [ "pytest" ]
    , py_modules        = [ "protostrings" ]
    , **vars(metadata)
    )
