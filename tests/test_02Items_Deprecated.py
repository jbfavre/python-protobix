#!/usr/bin/env python

# -*- coding: utf-8 -*-

import unittest
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import protobix

class TestDeprecatedItems(unittest.TestCase):

    data = {
        "myhost1": {
            "my.zabbix.item1": 0,
            "my.zabbix.item2": "item string"
        },
        "myhost2": {
            "my.zabbix.item1": 0,
            "my.zabbix.item2": "item string"
        }
    }
    data_type = 'items'

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

    def testBulkAddAndSent(self):
        self.zbx_container.data_type = self.data_type
        self.assertEqual(self.zbx_container.items_list, [])
        self.zbx_container.add(self.data)
        self.assertEqual(len(self.zbx_container.items_list), 4)
        ''' Send data to zabbix '''
        self.zbx_container.send()
        self.assertEqual(len(self.zbx_container.result), 1)
        for result in self.zbx_container.result:
            self.assertEqual(result[0], '4')
            self.assertEqual(result[1], '0')
            self.assertEqual(result[2], '4')
        self.assertEqual(self.zbx_container.items_list, [])

    def testDebugSent(self):
        self.zbx_container.debug = True
        self.zbx_container.data_type = self.data_type
        self.assertEqual(self.zbx_container.items_list, [])
        self.zbx_container.add(self.data)
        self.assertEqual(len(self.zbx_container.items_list), 4)
        ''' Send data to zabbix '''
        self.zbx_container.send()
        self.assertEqual(len(self.zbx_container.result), 4)
        for result in self.zbx_container.result: 
            self.assertEqual(result[0], '1')
            self.assertEqual(result[1], '0')
            self.assertEqual(result[2], '1')
        self.assertEqual(self.zbx_container.items_list, [])

    def testDryrunSent(self):
        self.zbx_container.data_type = self.data_type
        self.zbx_container.dryrun = True
        self.assertEqual(self.zbx_container.items_list, [])
        self.zbx_container.add(self.data)
        self.assertEqual(len(self.zbx_container.items_list), 4)
        ''' Send data to zabbix '''
        self.zbx_container.send()
        self.assertEqual(self.zbx_container.result, [['d', 'd', '4']])
        self.assertEqual(self.zbx_container.items_list, [])

    def testDryrunDebugSent(self):
        self.zbx_container.data_type = self.data_type
        self.zbx_container.dryrun = True
        self.zbx_container.debug = True
        self.assertEqual(self.zbx_container.items_list, [])
        self.zbx_container.add(self.data)
        self.assertEqual(len(self.zbx_container.items_list), 4)
        ''' Send data to zabbix '''
        self.assertEqual(self.zbx_container.result, [])
        self.zbx_container.send()
        for result in self.zbx_container.result:
            self.assertEqual(result, ['d', 'd', '1'])
        self.assertEqual(self.zbx_container.items_list, [])

    def testZabbixConnectionFails(self):
        self.zbx_container.zbx_port = 10052
        self.zbx_container.data_type = self.data_type
        self.assertEqual(self.zbx_container.items_list, [])
        self.zbx_container.add(self.data)
        ''' Send data to zabbix '''
        with self.assertRaises(protobix.SenderException):
            self.zbx_container.send()
        self.assertEqual(self.zbx_container.result, [])
        self.assertEqual(self.zbx_container.items_list, [])