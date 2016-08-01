"""
Tests for protobix.ZabbixAgentConfig
"""
import configobj
import pytest
import mock
import unittest

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import protobix

@mock.patch('configobj.ConfigObj')
def test_default_config_file(mock_configobj):
    """
    Default Zabbix Agent configuration from Zabbix
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig(
        'default_zabbix_agentd.conf'
    )
    assert zbx_config.server_active == '127.0.0.1'
    assert zbx_config.server_port == 10051
    assert zbx_config.log_type == 'file'
    assert zbx_config.log_file == '/tmp/zabbix_agentd.log'
    assert zbx_config.debug_level == 3
    assert zbx_config.timeout == 3
    assert zbx_config.hostname == 'Zabbix server'

@mock.patch('configobj.ConfigObj')
def test_not_found_config_file(mock_configobj):
    """
    Not found zabbix_agentd.conf
    hostname should fallback to socket.getfqdn
    """
    mock_configobj.side_effect = [
        {}
    ]
    with mock.patch('socket.getfqdn', return_value='myhostname'):
        zbx_config = protobix.ZabbixAgentConfig(
            'not_found_zabbix_agentd.conf'
        )
        assert zbx_config.server_active == '127.0.0.1'
        assert zbx_config.server_port == 10051
        assert zbx_config.hostname == 'myhostname'
        assert zbx_config.log_type == 'file'
        assert zbx_config.log_file == '/tmp/zabbix_agentd.log'
        assert zbx_config.debug_level == 3
        assert zbx_config.timeout == 3

@mock.patch('configobj.ConfigObj')
def test_server_active(mock_configobj):
    """
    Custom serverActive & serverPort
    """
    mock_configobj.side_effect = [
        {
            'ServerActive': 'myzabbixserver:10052,10.0.0.2:10051',
            'LogFile': '/tmp/zabbix_agentd.log',
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig(
        'zabbix_config_with_custom_serverActive'
    )
    assert zbx_config.server_active == 'myzabbixserver'
    assert zbx_config.server_port == 10052

@mock.patch('configobj.ConfigObj')
def test_server_active2(mock_configobj):
    """
    Invalid serverPort.
    Should raise an ValueError with proper message
    """
    mock_configobj.side_effect = [
        {
            'ServerActive': '127.0.0.1:1000',
            'LogFile': '/tmp/zabbix_agentd.log',
        }
    ]
    with pytest.raises(ValueError) as err:
        protobix.ZabbixAgentConfig(
            'zabbix_config_with_invalid_serverPort'
        )
    assert str(err.value) == 'ServerPort must be between 1024 and 32767'

@mock.patch('configobj.ConfigObj')
def test_server_active3(mock_configobj):
    """
    Invalid serverPort.
    Should raise an ValueError with proper message
    """
    mock_configobj.side_effect = [
        {
            'ServerActive': '127.0.0.1:40000',
            'LogFile': '/tmp/zabbix_agentd.log',
        }
    ]
    with pytest.raises(ValueError) as err:
        protobix.ZabbixAgentConfig(
            'zabbix_config_with_invalid_serverPort'
        )
    assert str(err.value) == 'ServerPort must be between 1024 and 32767'

@mock.patch('configobj.ConfigObj')
def test_log_type_log_file(mock_configobj):
    """
    LogType set to 'file' & LogFile set to '/tmp/zabbix_agentd.log'
    LogFile is mandatory
    """
    mock_configobj.side_effect = [
        {
            'LogType': 'file',
            'LogFile': '/tmp/test_zabbix_agentd.log',
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig(
        'zabbix_config_with_logType_to_file_logFile_set'
    )
    assert zbx_config.log_type == 'file'
    assert zbx_config.log_file == '/tmp/test_zabbix_agentd.log'

@mock.patch('configobj.ConfigObj')
def test_log_type_log_file2(mock_configobj):
    """
    LogType set to 'file' and LogFile not defined
    Should raise an ValueError with proper message
    """
    mock_configobj.side_effect = [
        {
            'LogType': 'file'
        }
    ]
    with pytest.raises(ValueError) as err:
        zbx_config = protobix.ZabbixAgentConfig(
            'zabbix_config_with_logType_to_system_logFile_empty'
        )
        assert zbx_config.log_type == 'file'
    assert str(err.value) == 'LogType set to file. LogFile is mandatory'

@mock.patch('configobj.ConfigObj')
def test_log_type_log_file3(mock_configobj):
    """
    LogType set to 'system'
    LogFile should be None
    """
    mock_configobj.side_effect = [
        {
            'LogType': 'system',
            'LogFile': '/tmp/zabbix_agentd.log',
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig(
        'zabbix_config_with_logType_to_system'
    )
    assert zbx_config.log_type == 'system'
    assert zbx_config.log_file is None

@mock.patch('configobj.ConfigObj')
def test_log_type_log_file4(mock_configobj):
    """
    LogType set to 'console'
    LogFile should be None
    """
    mock_configobj.side_effect = [
        {
            'LogType': 'console',
            'LogFile': '/tmp/zabbix_agentd.log',
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig(
        'zabbix_config_with_logType_to_console'
    )
    assert zbx_config.log_type == 'console'
    assert zbx_config.log_file is None

@mock.patch('configobj.ConfigObj')
def test_log_type_log_file5(mock_configobj):
    """
    LogType set to 'console'
    LogFile unset
    LogFile should be None
    """
    mock_configobj.side_effect = [
        {
            'LogType': 'console',
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig(
        'zabbix_config_with_logType_to_console'
    )
    assert zbx_config.log_type == 'console'
    assert zbx_config.log_file is None

@mock.patch('configobj.ConfigObj')
def test_log_type_log_file6(mock_configobj):
    """
    Invalid LogType
    Should raise an ValueError with proper message
    """
    mock_configobj.side_effect = [
        {
            'LogType': 'invalid',
        }
    ]
    with pytest.raises(ValueError) as err:
        protobix.ZabbixAgentConfig('zabbix_config_with_invalid_logType')
    assert str(err.value) == 'LogType must be one of [file,system,console]'

@mock.patch('configobj.ConfigObj')
def test_log_type_log_file7(mock_configobj):
    """
    Missing LogType & LogFile set to '-'
    LogType should fallbackback to system
    LogFile should fallback to '/dev/log'
    This is for Zabbix 2.4.x retro compatibility
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '-',
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig(
        'zabbix_config_with_missing_logType'
    )
    assert zbx_config.log_type == 'system'
    assert zbx_config.log_file is None

@mock.patch('configobj.ConfigObj')
def test_hostname(mock_configobj):
    """
    Custom hostname.
    Should *NOT* fallback to socket.getfqdn
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Hostname': 'myhostname'
        }
    ]
    with mock.patch('socket.getfqdn', return_value='myhostname.domain.tld'):
        zbx_config = protobix.ZabbixAgentConfig(
            'zabbix_config_with_custom_hostname'
        )
        assert zbx_config.hostname == 'myhostname'

@mock.patch('configobj.ConfigObj')
def test_timeout(mock_configobj):
    """
    Custom Timeout.
    Should not fallbackback to 3
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Timeout': 5,
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig(
        'zabbix_config_with_custom_timeout'
    )
    assert zbx_config.timeout == 5

@mock.patch('configobj.ConfigObj')
def test_timeout2(mock_configobj):
    """
    Invalid Timeout.
    Should raise an ValueError with proper message
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Timeout': -2,
        }
    ]
    with pytest.raises(ValueError) as err:
        protobix.ZabbixAgentConfig('zabbix_config_with_invalid_timeout')
    assert str(err.value) == 'Timeout must be between 1 and 30'

@mock.patch('configobj.ConfigObj')
def test_timeout3(mock_configobj):
    """
    Invalid Timeout.
    Should raise an ValueError with proper message
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Timeout': 50,
        }
    ]
    with pytest.raises(ValueError) as err:
        protobix.ZabbixAgentConfig('zabbix_config_with_invalid_timeout')
    assert str(err.value) == 'Timeout must be between 1 and 30'

@mock.patch('configobj.ConfigObj')
def test_debug_level(mock_configobj):
    """
    Custom DebugLevel.
    Should not fallbackback to 3
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'DebugLevel': 4
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig(
        'zabbix_config_with_custom_debugLevel'
    )
    assert zbx_config.debug_level == 4

@mock.patch('configobj.ConfigObj')
def test_debug_level2(mock_configobj):
    """
    Invalid DebugLevel.
    Should raise an ValueError with proper message
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'DebugLevel': -1
        }
    ]
    with pytest.raises(ValueError) as err:
        protobix.ZabbixAgentConfig('zabbix_config_with_invalid_debugLevel')
    assert str(err.value) == 'DebugLevel must be between 0 and 5'

@mock.patch('configobj.ConfigObj')
def test_debug_level3(mock_configobj):
    """
    Invalid DebugLevel.
    Should raise an ValueError with proper message
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'DebugLevel': 10
        }
    ]
    with pytest.raises(ValueError) as err:
        protobix.ZabbixAgentConfig('zabbix_config_with_invalid_debugLevel')
    assert str(err.value) == 'DebugLevel must be between 0 and 5'
