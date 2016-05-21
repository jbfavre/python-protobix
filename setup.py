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
    version = '0.1.1rc4',
    install_requires = [
        'configobj',
        'simplejson',
        'traceback2'
    ],

    description = 'Implementation of Zabbix Sender protocol',
    long_description = ( 'This module implements Zabbix Sender Protocol.\n'
                         'It allows to build list of items and send '
                         'them as trapper.\n'
                         'It currently supports items update as well as '
                         'Low Level Discovery.' ),    
    author = 'Jean Baptiste Favre',
    author_email = 'jean-baptiste.favre@blablacar.com',
    license = 'GPL-3+',
    url='https://github.com/jbfavre/python-protobix/',
    download_url = 'https://github.com/jbfavre/python-protobix/archive/0.1.1rc4.tar.gz',
    keywords = ['monitoring','zabbix','trappers'],
    classifiers = [],
    cmdclass={'test': PyTest}
   )
