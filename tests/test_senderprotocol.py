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

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig.server_active')
@mock.patch('protobix.ZabbixAgentConfig.server_port')
@mock.patch('protobix.ZabbixAgentConfig.timeout')
@mock.patch('protobix.ZabbixAgentConfig')
def test_default_params(mock_configobj, \
                        mock_server_active, \
                        mock_server_port, \
                        mock_timeout, \
                        mock_zabbix_agent_config):
    """
    Default configuration
    """
    mock_configobj.side_effect = [{
        'LogType': 'file',
        'LogFile': '/tmp/zabbix_agentd.log',
        'Server': '127.0.0.1',
        'ServerActive': '127.0.0.1',
        'Hostname': 'Zabbix server'
    }]
    mock_server_active.return_value = '127.0.0.1'
    mock_server_port.return_value = 10051
    mock_server_port.timeout.return_value = 3
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.zbx_host == '127.0.0.1'
    assert zbx_senderprotocol.zbx_port == 10051
    assert zbx_senderprotocol.dryrun is False
    assert zbx_senderprotocol.items_list == []
    assert zbx_senderprotocol._data is None
    assert zbx_senderprotocol.result is None

@mock.patch('configobj.ConfigObj')
def test_set_zbx_host(mock_configobj):
    """
    Test setting zbx_host
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    zbx_senderprotocol = protobix.SenderProtocol()
    zbx_senderprotocol.zbx_host = 'myserver'
    assert zbx_senderprotocol.zbx_host == 'myserver'

@mock.patch('configobj.ConfigObj')
def test_zbx_port(mock_configobj):
    """
    Test setting zbx_port with custom value
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.zbx_port == 10051
    zbx_senderprotocol.zbx_port = 10052
    assert zbx_senderprotocol.zbx_port == 10052

@mock.patch('configobj.ConfigObj')
def test_zbx_port2(mock_configobj):
    """
    Test setting zbx_port with invalid value
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    zbx_senderprotocol = protobix.SenderProtocol()
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol.zbx_port = 40000
    assert str(err.value) == 'ServerPort must be between 1024 and 32767'
    assert zbx_senderprotocol.zbx_port == 10051

@mock.patch('configobj.ConfigObj')
def test_zbx_port3(mock_configobj):
    """
    Test setting zbx_port with invalid value
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    zbx_senderprotocol = protobix.SenderProtocol()
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol.zbx_port = 1000
    assert str(err.value) == 'ServerPort must be between 1024 and 32767'
    assert zbx_senderprotocol.zbx_port == 10051

@mock.patch('configobj.ConfigObj')
def test_log_level(mock_configobj):
    """
    Test setting zbx_port with custom value
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.log_level == 3
    zbx_senderprotocol.log_level = 4
    assert zbx_senderprotocol.log_level == 4

@mock.patch('configobj.ConfigObj')
def test_log_level2(mock_configobj):
    """
    Test setting zbx_port with invalid value
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    zbx_senderprotocol = protobix.SenderProtocol()
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol.log_level = -1
    assert str(err.value) == 'DebugLevel must be between 0 and 5'
    assert zbx_senderprotocol.log_level == 3

@mock.patch('configobj.ConfigObj')
def test_log_level3(mock_configobj):
    """
    Test setting zbx_port with invalid value
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    zbx_senderprotocol = protobix.SenderProtocol()
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol.log_level = 10
    assert str(err.value) == 'DebugLevel must be between 0 and 5'
    assert zbx_senderprotocol.log_level == 3

@mock.patch('configobj.ConfigObj')
def test_zbx_server(mock_configobj):
    """
    Test setting zbx_server with custom value
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.zbx_host == '127.0.0.1'
    zbx_senderprotocol.zbx_host = 'myserver.domain.tld'
    assert zbx_senderprotocol.zbx_host == 'myserver.domain.tld'

@mock.patch('configobj.ConfigObj')
def test_dryrun(mock_configobj):
    """
    Test setting dryrun with custom value
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.dryrun == False
    zbx_senderprotocol.dryrun = True
    assert zbx_senderprotocol.dryrun == True

@mock.patch('configobj.ConfigObj')
def test_dryrun2(mock_configobj):
    """
    Test setting dryrun with invalid value
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.dryrun == False
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol.dryrun = 'invalid'
    assert str(err.value) == 'dryrun parameter requires boolean'
    assert zbx_senderprotocol.dryrun == False

@mock.patch('configobj.ConfigObj')
def test_clock(mock_configobj):
    """
    Test clock method
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    zbx_senderprotocol = protobix.SenderProtocol()
    assert isinstance(zbx_senderprotocol.clock, int) is True

@mock.patch('configobj.ConfigObj')
def test_clock2(mock_configobj):
    """
    Test clock method
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.clock == int(time.time())

#@mock.patch('configobj.ConfigObj')
#def test_send(mock_configobj):
#    """
#    Test clock method
#    """
#    
#    mock_configobj.side_effect = [
#        {
#            'LogFile': '/tmp/zabbix_agentd.log',
#            'Server': '127.0.0.1',
#            'ServerActive': '127.0.0.1',
#            'Hostname': 'Zabbix server'
#        }
#    ]
#    awaited_answer = json.loads(
#        '{"info": "processed: 0; failed: 1; total: 1; seconds spent: 0.000441", "response": "success"}'
#    )
#    with mock.patch('protobix.SenderProtocol._send_to_zabbix', return_value=awaited_answer):
#        zbx_senderprotocol = protobix.SenderProtocol()
#        zbx_senderprotocol.data_type='item'
#        item = { 'host': 'myhostname', 'key': 'my.item.key',
#                 'value': 1, 'clock': int(time.time())}
#        zbx_senderprotocol._items_list.append(item)
#        zbx_senderprotocol.send()
