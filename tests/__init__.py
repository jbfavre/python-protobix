#!/usr/bin/env python

import pytest

user_options = []
pytest_options = ['-v', '-k-_need_backend']
coverage_options = ['--cov', 'protobix', '--cov-report', 'term-missing']
pylint_options = ['--pylint ', '--pylint-error-types=WEF']
try: import coverage
except ImportError: coverage_options = []
try: import pylint
except ImportError: pylint_options = []
pytest_options += coverage_options
pytest_options += pylint_options
print(pytest_options)
errno = pytest.main(pytest_options)
raise SystemExit(errno)
