#!/usr/bin/env python

# pytest
# unittest
# mock
# tox

# -*- coding: utf-8 -*-

import pytest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import protobix

class TestItems:

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

    @classmethod
    def setup_class(cls):
        cls.zbx_container = protobix.DataContainer()

    @classmethod
    def teardown_class(cls):
        cls.zbx_container = None

    def testBulkAddAndSent(self):
        self.zbx_container.data_type = self.data_type
        assert self.zbx_container.items_list == []
        self.zbx_container.add(self.data)
        assert len(self.zbx_container.items_list) == 4
        ''' Send data to zabbix '''
        self.zbx_container.send()
        assert len(self.zbx_container.result) == 1
        for result in self.zbx_container.result:
            assert result[0] == '4'
            assert result[1] == '0'
            assert result[2] == '4'
        assert self.zbx_container.items_list == []

    def testDebugSent(self):
        self.zbx_container.dryrun = False
        self.zbx_container.debug = True
        self.zbx_container.zbx_port = 10051
        self.zbx_container.zbx_host = '127.0.0.1'
        self.zbx_container.data_type = self.data_type
        assert self.zbx_container.items_list == []
        self.zbx_container.add(self.data)
        assert len(self.zbx_container.items_list) == 4
        ''' Send data to zabbix '''
        self.zbx_container.send()
        assert len(self.zbx_container.result) == 4
        for result in self.zbx_container.result: 
            assert result[0] == '1'
            assert result[1] == '0'
            assert result[2] == '1'
        assert self.zbx_container.items_list == []

    def testDryrunSent(self):
        self.zbx_container.data_type = self.data_type
        self.zbx_container.dryrun = True
        self.zbx_container.log_level = 3
        self.zbx_container.zbx_port = 10051
        self.zbx_container.zbx_host = '127.0.0.1'
        assert self.zbx_container.items_list == []
        self.zbx_container.add(self.data)
        assert len(self.zbx_container.items_list) == 4
        ''' Send data to zabbix '''
        self.zbx_container.send()
        assert self.zbx_container.result == [['0', '0', '4']]
        assert self.zbx_container.items_list == []

    def testDryrunDebugSent(self):
        self.zbx_container.data_type = self.data_type
        self.zbx_container.dryrun = True
        self.zbx_container.log_level = 4
        self.zbx_container.zbx_port = 10051
        self.zbx_container.zbx_host = '127.0.0.1'
        assert self.zbx_container.items_list == []
        self.zbx_container.add(self.data)
        assert len(self.zbx_container.items_list) == 4
        ''' Send data to zabbix '''
        assert self.zbx_container.result == []
        self.zbx_container.send()
        for result in self.zbx_container.result:
            assert result == ['0', '0', '1']
        assert self.zbx_container.items_list == []

    def testServerConnectionFails(self):
        self.zbx_container.zbx_host = '127.0.1.1'
        self.zbx_container.zbx_port = 10052
        self.zbx_container.log_level = 3
        self.zbx_container.dryrun = False
        self.zbx_container.data_type = self.data_type
        assert self.zbx_container.items_list == []
        self.zbx_container.add(self.data)
        ''' Send data to zabbix '''
        with pytest.raises(protobix.SenderException):
            self.zbx_container.send()
        assert self.zbx_container.result == []
        assert self.zbx_container.items_list == []