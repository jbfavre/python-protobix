#!/usr/bin/env python

import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

class PyTest(TestCommand):
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import pytest
        options = "--cov protobix --cov-report term-missing"
        try: import coverage
        except ImportError: options = ""
        errno = pytest.main(options)
        raise SystemExit(errno)

setup(
    name = 'protobix',
    packages = ['protobix'],
    version = '0.0.9-rc1',
    install_requires = [
        'configobj',
        'logging',
        'functools',
        'simplejson',
        'traceback2'
    ],

    description = 'Implementation of Zabbix Sender protocol',
    long_description = ( 'This module implements Zabbix Sender Protocol.\n'
                         'It allows to build list of items and send items and send '
                         'them as trapper.\n'
                         'It currently supports items as well as Low Level Discovery.' ),    
    author = 'Jean Baptiste Favre',
    author_email = 'jean-baptiste.favre@blablacar.com',
    license = 'GPL',
    url='http://github.com/jbfavre/python-protobix/',
    download_url = 'http://github.com/jbfavre/python-protobix/tarball/0.0.9-beta1',
    keywords = ['monitoring','zabbix','trappers'],
    classifiers = [],
    cmdclass={'test': PyTest}
   )
