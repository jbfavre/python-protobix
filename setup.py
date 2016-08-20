#!/usr/bin/env python

import sys
from setuptools import setup

setup(
    name = 'protobix',
    packages = ['protobix'],
    version = '0.1.2',
    install_requires = [
        'configobj',
        'simplejson',
        'traceback2'
    ],
    tests_require = [
        'mock',
        'pytest>=2.7',
        'pytest-cov',
        'pytest-mock'
    ],
    test_suite='tests',
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
    download_url = 'https://github.com/jbfavre/python-protobix/archive/0.1.2.tar.gz',
    keywords = ['monitoring','zabbix','trappers'],
    classifiers = [],
   )
