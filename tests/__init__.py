#!/usr/bin/env python

import sys
import pytest
try:
    import coverage
    coverage_options = ['--cov', 'protobix', '--cov-report', 'term-missing']
except ImportError:
    coverage_options = []
try:
    import pylint
    pylint_options = ['--pylint ']
except ImportError:
    pylint_options = []

pytest_options = ['-v', '-k-_need_backend']
pytest_options += coverage_options
pytest_options += pylint_options

pytest.main(pytest_options)
