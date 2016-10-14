#!/usr/bin/env python

import sys
from setuptools import setup

setup(
    name = 'protobix',
    packages = ['protobix'],
    version = '1.0.0rc1',
    install_requires = [
        'configobj',
        'simplejson'
    ],
    tests_require = [
        'mock',
        'pytest',
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
    download_url = 'https://github.com/jbfavre/python-protobix/archive/1.0.0rc1.tar.gz',
    keywords = ['monitoring','zabbix','trappers'],
    classifiers = [],
   )
