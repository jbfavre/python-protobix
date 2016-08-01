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
    'myhost1': {
        'my.zabbix.lld_item1': [
            { '{#ZBX_LLD_KEY11}': 0,
              '{#ZBX_LLD_KEY12}': 'lld string' },
            { '{#ZBX_LLD_KEY11}': 1,
              '{#ZBX_LLD_KEY12}': 'another lld string' }
        ]
    },
    'myhost2': {
        'my.zabbix.lld_item2': [
            { '{#ZBX_LLD_KEY21}': 10,
              '{#ZBX_LLD_KEY21}': 'yet an lld string' },
            { '{#ZBX_LLD_KEY21}': 2,
              '{#ZBX_LLD_KEY21}': 'yet another lld string' }
        ]
    }
}
DATA_TYPE = 'lld'

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def testAddBeforeSettingData_type(mock_configobj, mock_zabbix_agent_config):
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
def testNoDebugNoDryrunSent(mock_configobj, mock_zabbix_agent_config):
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
    ''' Send data to zabbix '''
    ret = zbx_datacontainer.send()
    assert zbx_datacontainer.items_list == []
    assert len(zbx_datacontainer.result) == 1
    for result in zbx_datacontainer.result:
        assert result[0] == '2'
        assert result[1] == '0'
        assert result[2] == '2'
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
    zbx_datacontainer.log_level = 4
    zbx_datacontainer.data_type = DATA_TYPE
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA)
    assert len(zbx_datacontainer.items_list) == 2
    ''' Send data to zabbix '''
    ret = zbx_datacontainer.send()
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
    assert len(zbx_datacontainer.items_list) == 2
    ''' Send data to zabbix '''
    zbx_datacontainer.send()
    assert zbx_datacontainer.result == [['d', 'd', '2']]
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
    assert len(zbx_datacontainer.items_list) == 2
    ''' Send data to zabbix '''
    assert zbx_datacontainer.result == []
    zbx_datacontainer.send()
    for result in zbx_datacontainer.result:
        assert result == ['d', 'd', '1']
    assert zbx_datacontainer.items_list == []

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def testZabbixConnectionFails(mock_configobj, mock_zabbix_agent_config):
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
    ''' Send data to zabbix '''
    with pytest.raises(IOError):
        ret = zbx_datacontainer.send()
    assert zbx_datacontainer.items_list == []