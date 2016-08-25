"""
Tests for protobix.ZabbixAgentConfig
"""
import configobj
import pytest
import mock
import unittest
import logging

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import protobix

@mock.patch('configobj.ConfigObj')
def test_config_file_default(mock_configobj):
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
        config_file='default_zabbix_agentd.conf'
    )
    assert zbx_config.data_type is None
    assert zbx_config.dryrun is False
    assert zbx_config.server_active == '127.0.0.1'
    assert zbx_config.server_port == 10051
    assert zbx_config.log_type == 'file'
    assert zbx_config.log_file == '/tmp/zabbix_agentd.log'
    assert zbx_config.debug_level == 3
    assert zbx_config.timeout == 3
    assert zbx_config.hostname == 'Zabbix server'
    assert zbx_config.tls_connect == 'unencrypted'
    assert zbx_config.tls_ca_file is None
    assert zbx_config.tls_cert_file is None
    assert zbx_config.tls_crl_file is None
    assert zbx_config.tls_key_file is None
    assert zbx_config.tls_server_cert_issuer is None
    assert zbx_config.tls_server_cert_subject is None
    assert zbx_config.tls_psk_identity is None
    assert zbx_config.tls_psk_file is None

@mock.patch('configobj.ConfigObj')
def test_config_file_not_found(mock_configobj):
    """
    Not found zabbix_agentd.conf
    hostname should fallback to socket.getfqdn
    """
    mock_configobj.side_effect = [
        {}
    ]
    with mock.patch('socket.getfqdn', return_value='myhostname'):
        zbx_config = protobix.ZabbixAgentConfig(
            config_file='not_found_config_file'
        )
        assert zbx_config.data_type is None
        assert zbx_config.dryrun is False
        assert zbx_config.server_active == '127.0.0.1'
        assert zbx_config.server_port == 10051
        assert zbx_config.log_type == 'file'
        assert zbx_config.log_file == '/tmp/zabbix_agentd.log'
        assert zbx_config.debug_level == 3
        assert zbx_config.timeout == 3
        assert zbx_config.hostname == 'myhostname'
        assert zbx_config.tls_connect == 'unencrypted'
        assert zbx_config.tls_ca_file is None
        assert zbx_config.tls_cert_file is None
        assert zbx_config.tls_crl_file is None
        assert zbx_config.tls_key_file is None
        assert zbx_config.tls_server_cert_issuer is None
        assert zbx_config.tls_server_cert_subject is None
        assert zbx_config.tls_psk_identity is None
        assert zbx_config.tls_psk_file is None

@mock.patch('configobj.ConfigObj')
def test_server_active_custom(mock_configobj):
    """
    Custom serverActive & serverPort
    """
    mock_configobj.side_effect = [
        {
            'ServerActive': 'myzabbixserver:10052,10.0.0.2:10051',
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig(
        'zabbix_config_with_custom_serverActive'
    )
    assert zbx_config.server_active == 'myzabbixserver'
    assert zbx_config.server_port == 10052

@mock.patch('configobj.ConfigObj')
def test_server_port_invalid_lower_than_1024(mock_configobj):
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
def test_server_port_invalid_greater_than_32767(mock_configobj):
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
def test_log_config_custom(mock_configobj):
    """
    LogType set to 'file'
    LogFile set to '/tmp/zabbix_agentd.log'
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
def test_log_config_fallback_log_file(mock_configobj):
    """
    LogType set to 'file'
    LogFile unset
    LogFile should default to '/tmp/zabbix_agentd.log'
    """
    mock_configobj.side_effect = [
        {
            'LogType': 'file'
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig(
        'zabbix_config_with_logType_to_system_logFile_empty'
    )
    assert zbx_config.log_type == 'file'
    assert zbx_config.log_file == '/tmp/zabbix_agentd.log'

@mock.patch('configobj.ConfigObj')
def test_log_config_use_syslog(mock_configobj):
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
def test_log_config_use_console(mock_configobj):
    """
    LogType set to 'console'
    LogFile set
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
def test_log_config_use_console_fallback_log_file(mock_configobj):
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
def test_log_config_invalid_log_type(mock_configobj):
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
def test_log_config_zabbix_24_compatibility(mock_configobj):
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
def test_hostname_custom(mock_configobj):
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
def test_timeout_custom(mock_configobj):
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
def test_timeout_invalid_lower_than_0(mock_configobj):
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
def test_timeout_invalid_greater_than_30(mock_configobj):
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
def test_debug_level_custom(mock_configobj):
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
def test_debug_level_invalid_lower_than_0(mock_configobj):
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
    assert str(err.value) == 'DebugLevel must be between 0 and 5, -1 provided'

@mock.patch('configobj.ConfigObj')
def test_debug_level_invalid_greater_than_5(mock_configobj):
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
    assert str(err.value) == 'DebugLevel must be between 0 and 5, 10 provided'

@mock.patch('configobj.ConfigObj')
def test_tls_default_config(mock_configobj):
    """
    Default TLS configuration
    """
    mock_configobj.side_effect = [{}]
    zbx_config = protobix.ZabbixAgentConfig('TLS_default_configuration')
    assert zbx_config.tls_connect == 'unencrypted'
    assert zbx_config.tls_ca_file is None
    assert zbx_config.tls_cert_file is None
    assert zbx_config.tls_crl_file is None
    assert zbx_config.tls_key_file is None
    assert zbx_config.tls_server_cert_issuer is None
    assert zbx_config.tls_server_cert_subject is None

@mock.patch('configobj.ConfigObj')
def test_tls_connect_unencrypted_other_custom(mock_configobj):
    """
    TLSConnect: 'unencrypted'
    All other TLS parameters should default to None
    """
    mock_configobj.side_effect = [
        {
            'TLSConnect': 'unencrypted',
            'TLSCAFile': '/tmp/tls_ca_file.crt',
            'TLSCertFile': '/tmp/tls_cert_file.crt',
            'TLSCRLFile': '/tmp/tls_crl_file.crt',
            'TLSKeyFile': '/tmp/tls_ckey_file.crt',
            'TLSServerCertIssuer': '/tmp/tls_server__cert_issuer.crt',
            'TLSServerCertSubject': '/tmp/tls_server_cert_subject.crt',
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig('TLSConnect_unencrypted')
    assert zbx_config.tls_connect == 'unencrypted'
    assert zbx_config.tls_ca_file is None
    assert zbx_config.tls_cert_file is None
    assert zbx_config.tls_crl_file is None
    assert zbx_config.tls_key_file is None
    assert zbx_config.tls_server_cert_issuer is None
    assert zbx_config.tls_server_cert_subject is None

@mock.patch('configobj.ConfigObj')
def test_tls_connect_cert_tls_cert_key_missing(mock_configobj):
    """
    TLSConnect: 'cert'
    TLSCertFile unset
    TLSKeyFile unset
    Should raise a ValueError with appropriate message
    """
    mock_configobj.side_effect = [
        {
            'TLSConnect': 'cert'
        }
    ]
    with pytest.raises(ValueError) as err:
        protobix.ZabbixAgentConfig('TLSConnect_cert_without_TLSCertFile_TLSKeyFile_TLSCAFile')
    assert str(err.value) == 'TLSConnect is cert. TLSCertFile, TLSKeyFile and TLSCAFile are mandatory'

@mock.patch('configobj.ConfigObj')
def test_tls_connect_cert_tls_cert_key_custom(mock_configobj):
    """
    TLSConnect: 'cert'
    TLSCertFile set
    TLSKeyFile set
    """
    mock_configobj.side_effect = [
        {
            'TLSConnect': 'cert',
            'TLSCertFile': '/tmp/tls_cert_file.pem',
            'TLSKeyFile': '/tmp/tls_key_file.pem',
            'TLSCAFile': '/tmp/tls_ca_file.pem',
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig('TLSConnect_TLSCertFile_TLSKeyFile')
    assert zbx_config.tls_connect == 'cert'
    assert zbx_config.tls_cert_file == '/tmp/tls_cert_file.pem'
    assert zbx_config.tls_key_file == '/tmp/tls_key_file.pem'
    assert zbx_config.tls_ca_file == '/tmp/tls_ca_file.pem'


@mock.patch('configobj.ConfigObj')
def test_tls_connect_cert_other_custom(mock_configobj):
    """
    TLSConnect: 'cert'
    Other TLS params custom
    """
    mock_configobj.side_effect = [
        {
            'TLSConnect': 'cert',
            'TLSCAFile': '/tmp/tls_ca_file.crt',
            'TLSCertFile': '/tmp/tls_cert_file.crt',
            'TLSCRLFile': '/tmp/tls_crl_file.crt',
            'TLSKeyFile': '/tmp/tls_key_file.crt',
            'TLSServerCertIssuer': '/tmp/tls_server__cert_issuer.crt',
            'TLSServerCertSubject': '/tmp/tls_server_cert_subject.crt',
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig('TLSConnect_TLSCertFile_TLSKeyFile')
    assert zbx_config.tls_connect == 'cert'
    assert zbx_config.tls_ca_file == '/tmp/tls_ca_file.crt'
    assert zbx_config.tls_cert_file == '/tmp/tls_cert_file.crt'
    assert zbx_config.tls_crl_file == '/tmp/tls_crl_file.crt'
    assert zbx_config.tls_key_file == '/tmp/tls_key_file.crt'
    assert zbx_config.tls_server_cert_issuer == '/tmp/tls_server__cert_issuer.crt'
    assert zbx_config.tls_server_cert_subject == '/tmp/tls_server_cert_subject.crt'

@mock.patch('configobj.ConfigObj')
def test_tls_connect_invalid(mock_configobj):
    """
    invalid TLSConnect
    Should raise a ValueError with appropriate message
    """
    mock_configobj.side_effect = [
        {
            'TLSConnect': 'invalid',
        }
    ]
    with pytest.raises(ValueError) as err:
        protobix.ZabbixAgentConfig('TLSConnect_invalid')
    assert str(err.value) == 'TLSConnect must be one of [unencrypted,psk,cert]'

@mock.patch('configobj.ConfigObj')
def test_tls_connect_psk_tls_msk_identity_file_missing(mock_configobj):
    """
    TLSConnect: 'psk'
    Should raise a NotImplementedError with appropriate message
    """
    mock_configobj.side_effect = [
        {
            'TLSConnect': 'psk'
        }
    ]
    with pytest.raises(ValueError) as err:
        protobix.ZabbixAgentConfig('TLSConnect_psk')
    assert str(err.value) == 'TLSConnect is psk. TLSPSKIdentity and TLSPSKFile are mandatory'

@mock.patch('configobj.ConfigObj')
def test_tls_connect_psk(mock_configobj):
    """
    TLSConnect: 'psk'
    Should raise a NotImplementedError with appropriate message
    """
    mock_configobj.side_effect = [
        {
            'TLSConnect': 'psk',
            'TLSPSKIdentity': 'TLS PSK Zabbix Identity',
            'TLSPSKFile': '/tmp/psk.file',
        }
    ]
    zbx_config = protobix.ZabbixAgentConfig('TLSConnect_psk')
    assert zbx_config.tls_psk_identity == 'TLS PSK Zabbix Identity'
    assert zbx_config.tls_psk_file == '/tmp/psk.file'

@mock.patch('configobj.ConfigObj')
def test_data_type(mock_configobj):
    """
    Test data_type. Default is None
    """
    mock_configobj.side_effect = [{}]
    zbx_config = protobix.ZabbixAgentConfig('default_configuration')
    assert zbx_config.data_type is None
    zbx_config.data_type = 'items'
    assert zbx_config.data_type == 'items'
    zbx_config.data_type = 'lld'
    assert zbx_config.data_type == 'lld'

@mock.patch('configobj.ConfigObj')
def test_data_type_invalid(mock_configobj):
    """
    Test data_type with invalid value
    """
    mock_configobj.side_effect = [{}]
    zbx_config = protobix.ZabbixAgentConfig('default_configuration')
    assert zbx_config.data_type is None
    with pytest.raises(ValueError) as err:
        zbx_config.data_type = 'invalid'
    assert str(err.value) == 'data_type requires either "items" or "lld"'
    assert zbx_config.data_type is None

@mock.patch('configobj.ConfigObj')
def test_dryrun(mock_configobj):
    """
    Test dryrun. Default is False
    """
    mock_configobj.side_effect = [{}]
    zbx_config = protobix.ZabbixAgentConfig('default_configuration')
    assert zbx_config.dryrun is False
    zbx_config.dryrun = True
    assert zbx_config.dryrun is True

@mock.patch('configobj.ConfigObj')
def test_dryrun_invalid(mock_configobj):
    """
    Test dryrun with invalid value
    """
    mock_configobj.side_effect = [{}]
    zbx_config = protobix.ZabbixAgentConfig('default_configuration')
    assert zbx_config.dryrun is False
    with pytest.raises(ValueError) as err:
        zbx_config.dryrun = 'invalid'
    assert str(err.value) == 'dryrun parameter requires boolean'
    assert zbx_config.dryrun is False
