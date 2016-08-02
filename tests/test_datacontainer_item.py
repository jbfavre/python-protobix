"""
Tests for protobix.SenderProtocol
"""
import configobj
import pytest
import mock
import unittest
import time
try: import simplejson as json
except ImportError: import json
import socket

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import protobix

DATA = {
    "myhost1": {
        "my.zabbix.item1": 0,
        "my.zabbix.item2": "item string"
    },
    "myhost2": {
        "my.zabbix.item1": 0,
        "my.zabbix.item2": "item string"
    }
}
DATA_TYPE = 'items'

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_items_add_before_set_data_type(mock_configobj, mock_zabbix_agent_config):
    """
    Adding data before assigning data_type should raise an Exception
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    assert zbx_datacontainer.items_list == []
    with pytest.raises(ValueError):
        zbx_datacontainer.add(DATA)
    assert zbx_datacontainer.items_list == []

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_send_debug_level_no_dryrun_no(mock_configobj, mock_zabbix_agent_config):
    """
    debug_level to False
    dryrun to False
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.data_type = DATA_TYPE
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA)
    assert len(zbx_datacontainer.items_list) == 4
    zbx_datacontainer.send()
    assert len(zbx_datacontainer.result) == 1
    for result in zbx_datacontainer.result:
        assert result[0] == '4'
        assert result[1] == '0'
        assert result[2] == '4'
    assert zbx_datacontainer.items_list == []

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def testDebugNoDryrunSent(mock_configobj, mock_zabbix_agent_config):
    """
    debug_level to True
    dryrun to False
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.data_type = DATA_TYPE
    zbx_datacontainer.log_level = 4
    zbx_datacontainer.add(DATA)
    assert len(zbx_datacontainer.items_list) == 4
    zbx_datacontainer.send()
    assert len(zbx_datacontainer.result) == 4
    for result in zbx_datacontainer.result:
        assert result[0] == '1'
        assert result[1] == '0'
        assert result[2] == '1'
    assert zbx_datacontainer.items_list == []

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def testNoDebugDryrunSent(mock_configobj, mock_zabbix_agent_config):
    """
    debug_level to False
    dryrun to True
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.data_type = DATA_TYPE
    zbx_datacontainer.dryrun = True
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA)
    assert len(zbx_datacontainer.items_list) == 4
    zbx_datacontainer.send()
    assert zbx_datacontainer.result == [['d', 'd', '4']]
    assert zbx_datacontainer.items_list == []

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def testDebugDryrunSent(mock_configobj, mock_zabbix_agent_config):
    """
    debug_level to True
    dryrun to True
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.data_type = DATA_TYPE
    zbx_datacontainer.dryrun = True
    zbx_datacontainer.log_level = 4
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA)
    assert len(zbx_datacontainer.items_list) == 4
    assert zbx_datacontainer.result == []
    zbx_datacontainer.send()
    for result in zbx_datacontainer.result:
        assert result == ['d', 'd', '1']
    assert zbx_datacontainer.items_list == []

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def testServerConnectionFails(mock_configobj, mock_zabbix_agent_config):
    """
    Connection to Zabbix Server fails
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.zbx_port = 10052
    zbx_datacontainer.data_type = DATA_TYPE
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA)
    with pytest.raises(IOError):
        zbx_datacontainer.send()
    assert zbx_datacontainer.result == []
    assert zbx_datacontainer.items_list == []
