#!/usr/bin/env python

# -*- coding: utf-8 -*-

import unittest

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import protobix
import time

class TestDeprecatedDataContainer(unittest.TestCase):

  def setUp(self):
    self.zbx_container = protobix.DataContainer()
    self.zbx_container._items_list = []
    self.zbx_container._config = {
        'server': '127.0.0.1',
        'port': 10051,
        'log_level': 3,
        'log_output': '/tmp/zabbix_agentd.log',
        'dryrun': False,
        'data_type': None,
        'timeout': 3,
    }

  def tearDown(self):
    self.zbx_container._items_list = []
    self.zbx_container._config = {
        'server': '127.0.0.1',
        'port': 10051,
        'log_level': 3,
        'log_output': '/tmp/zabbix_agentd.log',
        'dryrun': False,
        'data_type': None,
        'timeout': 3,
    }
    self.zbx_container = None

  def test_01DefaultValues(self):
    self.assertEqual(self.zbx_container.zbx_host, '127.0.0.1')
    self.assertEqual(self.zbx_container.zbx_port, 10051)
    self.assertEqual(self.zbx_container.data_type, None)
    self.assertEqual(self.zbx_container.debug, False)
    self.assertEqual(self.zbx_container.dryrun, False)
    self.assertEqual(self.zbx_container.items_list, [])

  def test_02DataType(self):
    self.zbx_container.data_type = 'items'
    self.assertEqual(self.zbx_container.data_type, 'items')
    self.zbx_container.data_type = 'lld'
    self.assertEqual(self.zbx_container.data_type, 'lld')
    with self.assertRaises(ValueError):
      self.zbx_container.data_type = 'bad'

  def test_03ZabbixHostAndPort(self):
    self.zbx_container.zbx_host = 'localhost'
    self.assertEqual(self.zbx_container.zbx_host, 'localhost')
    self.zbx_container.zbx_port = 10052
    self.assertEqual(self.zbx_container.zbx_port, 10052)

  def test_04Debug(self):
    for value in [True, False]:
      self.zbx_container.debug = value
      self.assertEqual(self.zbx_container.debug, value)
    with self.assertRaises(ValueError):
      self.zbx_container.debug = 'bad'

  def test_05DryRun(self):
    for value in [True, False]:
      self.zbx_container.dryrun = value
      self.assertEqual(self.zbx_container.dryrun, value)
    with self.assertRaises(ValueError):
      self.zbx_container.dryrun = 'bad'