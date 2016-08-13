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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import protobix

DATA = {
    'items': {
        "protobix.host1": {
            "my.protobix.item.int": 0,
            "my.protobix.item.string": "item string"
        },
        "protobix.host2": {
            "my.protobix.item.int": 0,
            "my.protobix.item.string": "item string"
        }
    },
    'lld': {
        'protobix.host1': {
            'my.protobix.lld_item1': [
                { '{#PBX_LLD_KEY11}': 0,
                  '{#PBX_LLD_KEY12}': 'lld string' },
                { '{#PBX_LLD_KEY11}': 1,
                  '{#PBX_LLD_KEY12}': 'another lld string' }
            ],
            'my.protobix.lld_item2': [
                { '{#PBX_LLD_KEY21}': 10,
                  '{#PBX_LLD_KEY21}': 'yet an lld string' },
                { '{#PBX_LLD_KEY21}': 2,
                  '{#PBX_LLD_KEY21}': 'yet another lld string' }
            ]

        },
        'protobix.host2': {
            'my.protobix.lld_item1': [
                { '{#PBX_LLD_KEY11}': 0,
                  '{#PBX_LLD_KEY12}': 'lld string' },
                { '{#PBX_LLD_KEY11}': 1,
                  '{#PBX_LLD_KEY12}': 'another lld string' }
            ],
            'my.protobix.lld_item2': [
                { '{#PBX_LLD_KEY21}': 10,
                  '{#PBX_LLD_KEY21}': 'yet an lld string' },
                { '{#PBX_LLD_KEY21}': 2,
                  '{#PBX_LLD_KEY21}': 'yet another lld string' }
            ]
        }
    }
}

pytest_params = (
    'items',
    'lld'
)
@pytest.mark.parametrize('data_type', pytest_params)
@mock.patch('protobix.ZabbixAgentConfig')
@mock.patch('configobj.ConfigObj')
def test_items_add_before_set_data_type(mock_configobj, mock_zabbix_agent_config, data_type):
    """
    Adding data before assigning data_type should raise an Exception
    """
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    assert zbx_datacontainer.items_list == []
    with pytest.raises(ValueError):
        zbx_datacontainer.add(DATA[data_type])
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.data_type = data_type
    zbx_datacontainer.add(DATA)
    assert len(zbx_datacontainer.items_list) == 4

@pytest.mark.parametrize('data_type', pytest_params)
@mock.patch('protobix.ZabbixAgentConfig')
@mock.patch('configobj.ConfigObj')
def test_debug_no_dryrun_yes(mock_configobj, mock_zabbix_agent_config, data_type):
    """
    debug_level to False
    dryrun to True
    """
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.data_type = data_type
    zbx_datacontainer.dryrun = True
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA[data_type])
    assert len(zbx_datacontainer.items_list) == 4

    assert zbx_datacontainer.dryrun is True
    assert zbx_datacontainer.debug_level < 4

    ''' Send data to zabbix '''
    results_list = zbx_datacontainer.send()
    assert results_list == [['d', 'd', '4', 'd']]
    assert zbx_datacontainer.items_list == []

@pytest.mark.parametrize('data_type', pytest_params)
@mock.patch('protobix.ZabbixAgentConfig')
@mock.patch('configobj.ConfigObj')
def test_debug_yes_dryrun_yes(mock_configobj, mock_zabbix_agent_config, data_type):
    """
    debug_level to True
    dryrun to True
    """
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.data_type = data_type
    zbx_datacontainer.dryrun = True
    zbx_datacontainer.debug_level = 4
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA[data_type])
    assert len(zbx_datacontainer.items_list) == 4

    assert zbx_datacontainer.dryrun is True
    assert zbx_datacontainer.debug_level >= 4

    ''' Send data to zabbix '''
    results_list = zbx_datacontainer.send()
    for result in results_list:
        assert result == ['d', 'd', '1', 'd']
    assert zbx_datacontainer.items_list == []

@pytest.mark.parametrize('data_type', pytest_params)
@mock.patch('protobix.ZabbixAgentConfig')
@mock.patch('configobj.ConfigObj')
def test_debug_no_dryrun_no(mock_configobj, mock_zabbix_agent_config, data_type):
    """
    debug_level to False
    dryrun to False
    """
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    # Force a Zabbix port so that test fails even if backend is present
    zbx_datacontainer.server_port = 10060
    zbx_datacontainer.data_type = data_type
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA[data_type])
    assert len(zbx_datacontainer.items_list) == 4

    assert zbx_datacontainer.dryrun is False
    assert zbx_datacontainer.debug_level < 4

    ''' Send data to zabbix '''
    with pytest.raises(socket.error):
        results_list = zbx_datacontainer.send()

@pytest.mark.parametrize('data_type', pytest_params)
@mock.patch('protobix.ZabbixAgentConfig')
@mock.patch('configobj.ConfigObj')
def test_debug_yes_dryrun_no(mock_configobj, mock_zabbix_agent_config, data_type):
    """
    debug_level to True
    dryrun to False
    """
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.debug_level = 4
    # Force a Zabbix port so that test fails even if backend is present
    zbx_datacontainer.server_port = 10060
    zbx_datacontainer.data_type = data_type
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA[data_type])
    assert len(zbx_datacontainer.items_list) == 4

    assert zbx_datacontainer.dryrun is False
    assert zbx_datacontainer.debug_level >= 4

    ''' Send data to zabbix '''
    with pytest.raises(socket.error):
        results_list = zbx_datacontainer.send()

@pytest.mark.parametrize('data_type', pytest_params)
@mock.patch('protobix.ZabbixAgentConfig')
@mock.patch('configobj.ConfigObj')
def test_need_backend_debug_no_dryrun_no(mock_configobj, mock_zabbix_agent_config, data_type):
    """
    debug_level to False
    dryrun to False
    """
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.data_type = data_type
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA[data_type])
    assert len(zbx_datacontainer.items_list) == 4

    assert zbx_datacontainer.dryrun is False
    assert zbx_datacontainer.debug_level < 4

    ''' Send data to zabbix '''
    results_list = zbx_datacontainer.send()
    assert zbx_datacontainer.items_list == []
    assert len(results_list) == 1
    for result in results_list:
        assert result[0] == '4'
        assert result[1] == '0'
        assert result[2] == '4'
    assert zbx_datacontainer.items_list == []

@pytest.mark.parametrize('data_type', pytest_params)
@mock.patch('protobix.ZabbixAgentConfig')
@mock.patch('configobj.ConfigObj')
def test_need_backend_debug_yes_dryrun_no(mock_configobj, mock_zabbix_agent_config, data_type):
    """
    debug_level to True
    dryrun to False
    """
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.debug_level = 4
    zbx_datacontainer.data_type = data_type
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA[data_type])
    assert len(zbx_datacontainer.items_list) == 4

    assert zbx_datacontainer.dryrun is False
    assert zbx_datacontainer.debug_level >= 4

    ''' Send data to zabbix '''
    results_list = zbx_datacontainer.send()
    assert len(results_list) == 4
    for result in results_list:
        assert result[0] == '1'
        assert result[1] == '0'
        assert result[2] == '1'
    assert zbx_datacontainer.items_list == []

@pytest.mark.parametrize('data_type', pytest_params)
@mock.patch('protobix.ZabbixAgentConfig')
@mock.patch('configobj.ConfigObj')
def test_server_connection_fails(mock_configobj, mock_zabbix_agent_config, data_type):
    """
    Connection to Zabbix Server fails
    """
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.server_port = 10060
    zbx_datacontainer.data_type = data_type
    assert zbx_datacontainer.items_list == []
    assert zbx_datacontainer.server_port == 10060
    zbx_datacontainer.add(DATA[data_type])
    with pytest.raises(IOError):
        zbx_datacontainer.send()
    assert zbx_datacontainer.items_list == []
