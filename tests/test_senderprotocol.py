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
import ssl

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import protobix

try: import simplejson as json
except ImportError: import json
import struct
if sys.version_info < (3,):
    def b(x):
        return x
else:
    import codecs
    def b(x):
        return codecs.utf_8_encode(x)[0]

@mock.patch('protobix.ZabbixAgentConfig')
@mock.patch('configobj.ConfigObj')
def test_default_params(mock_configobj, \
                        mock_zabbix_agent_config):
    """
    Default configuration
    """
    print('ConfigObj ' + str(mock_configobj))
    print('ZabbixAgentConfig ' + str(mock_zabbix_agent_config))

    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    mock_zabbix_agent_config.server_active.return_value = '127.0.0.1'
    mock_zabbix_agent_config.server_port.return_value = 10051
    mock_zabbix_agent_config.server_port.timeout.return_value = 3
    zbx_senderprotocol = protobix.SenderProtocol()

    assert zbx_senderprotocol.server_active == '127.0.0.1'
    assert zbx_senderprotocol.server_port == 10051
    assert zbx_senderprotocol._config.dryrun is False
    assert zbx_senderprotocol.items_list == []

@mock.patch('configobj.ConfigObj')
def test_server_active_custom(mock_configobj):
    """
    Test setting zbx_server with custom value
    """
    mock_configobj.side_effect = [{}]
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.server_active == '127.0.0.1'
    zbx_senderprotocol.server_active = 'myserver.domain.tld'
    assert zbx_senderprotocol.server_active == 'myserver.domain.tld'

@mock.patch('configobj.ConfigObj')
def test_server_port_custom(mock_configobj):
    """
    Test setting server_port with custom value
    """
    mock_configobj.side_effect = [{}]
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.server_port == 10051
    zbx_senderprotocol.server_port = 10052
    assert zbx_senderprotocol.server_port == 10052

@mock.patch('configobj.ConfigObj')
def test_server_port_invalid_greater_than_32767(mock_configobj):
    """
    Test setting server_port with invalid value
    """
    mock_configobj.side_effect = [{}]
    zbx_senderprotocol = protobix.SenderProtocol()
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol.server_port = 40000
    assert str(err.value) == 'ServerPort must be between 1024 and 32767'
    assert zbx_senderprotocol.server_port == 10051

@mock.patch('configobj.ConfigObj')
def test_server_port_invalid_lower_than_1024(mock_configobj):
    """
    Test setting server_port with invalid value
    """
    mock_configobj.side_effect = [{}]
    zbx_senderprotocol = protobix.SenderProtocol()
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol.server_port = 1000
    assert str(err.value) == 'ServerPort must be between 1024 and 32767'
    assert zbx_senderprotocol.server_port == 10051

@mock.patch('configobj.ConfigObj')
def test_debug_custom(mock_configobj):
    """
    Test setting server_port with custom value
    """
    mock_configobj.side_effect = [{}]
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.debug_level == 3
    zbx_senderprotocol.debug_level = 4
    assert zbx_senderprotocol.debug_level == 4

@mock.patch('configobj.ConfigObj')
def test_debug_invalid_lower_than_0(mock_configobj):
    """
    Test setting server_port with invalid value
    """
    mock_configobj.side_effect = [{}]
    zbx_senderprotocol = protobix.SenderProtocol()
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol.debug_level = -1
    assert str(err.value) == 'DebugLevel must be between 0 and 5, -1 provided'
    assert zbx_senderprotocol.debug_level == 3

@mock.patch('configobj.ConfigObj')
def test_debug_invalid_greater_than_5(mock_configobj):
    """
    Test setting server_port with invalid value
    """
    mock_configobj.side_effect = [{}]
    zbx_senderprotocol = protobix.SenderProtocol()
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol.debug_level = 10
    assert str(err.value) == 'DebugLevel must be between 0 and 5, 10 provided'
    assert zbx_senderprotocol.debug_level == 3

@mock.patch('configobj.ConfigObj')
def test_dryrun_custom(mock_configobj):
    """
    Test setting dryrun with custom value
    """
    mock_configobj.side_effect = [{}]
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol._config.dryrun is False
    zbx_senderprotocol._config.dryrun = True
    assert zbx_senderprotocol._config.dryrun is True
    zbx_senderprotocol._config.dryrun = False
    assert zbx_senderprotocol._config.dryrun is False

@mock.patch('configobj.ConfigObj')
def test_dryrun_invalid(mock_configobj):
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
    assert zbx_senderprotocol._config.dryrun is False
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol._config.dryrun = 'invalid'
    assert str(err.value) == 'dryrun parameter requires boolean'
    assert zbx_senderprotocol._config.dryrun is False

@mock.patch('configobj.ConfigObj')
def test_clock_integer(mock_configobj):
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
def test_clock_accurate(mock_configobj):
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

@mock.patch('configobj.ConfigObj')
@mock.patch('socket.socket', return_value=mock.MagicMock(name='socket', spec=socket.socket))
def test_send_to_zabbix(mock_configobj, mock_socket):
    """
    Test sending data to Zabbix Server
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    item = { 'host': 'myhostname', 'key': 'my.item.key',
             'value': 1, 'clock': int(time.time())}
    payload = json.dumps({
        "data": [item],
        "request": "sender data",
        "clock": int(time.time())
    })
    packet = b('ZBXD\1') + struct.pack('<Q', 136) + b(payload)

    zbx_senderprotocol = protobix.SenderProtocol()
    zbx_senderprotocol.socket = mock_socket
    zbx_senderprotocol.data_type='item'
    zbx_senderprotocol._items_list.append(item)
    zbx_senderprotocol._send_to_zabbix(zbx_senderprotocol._items_list)

    zbx_senderprotocol.socket.sendall.assert_called_with(packet)

@mock.patch('configobj.ConfigObj')
@mock.patch('socket.socket', return_value=mock.MagicMock(name='socket', spec=socket.socket))
def test_send_to_zabbix_dryrun(mock_configobj, mock_socket):
    """
    Test sending data to Zabbix Server
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
    zbx_senderprotocol.data_type='item'
    zbx_senderprotocol._config.dryrun = True
    result = zbx_senderprotocol._send_to_zabbix(zbx_senderprotocol._items_list)
    assert result == 0

@mock.patch('configobj.ConfigObj')
@mock.patch('socket.socket', return_value=mock.MagicMock(name='socket', spec=socket.socket))
def test_read_from_zabbix(mock_configobj, mock_socket):
    """
    Test sending data to Zabbix Server
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server'
        }
    ]
    answer_payload = '{"info": "processed: 0; failed: 1; total: 1; seconds spent: 0.000441", "response": "success"}'
    answer_packet = b('ZBXD\1') + struct.pack('<Q', 93) + b(answer_payload)
    mock_socket.recv.return_value = answer_packet
    answer_awaited = json.loads(answer_payload)

    zbx_senderprotocol = protobix.SenderProtocol()
    zbx_senderprotocol.data_type='item'
    zbx_senderprotocol.socket = mock_socket
    result = zbx_senderprotocol._read_from_zabbix()
    assert result == answer_awaited

@mock.patch('configobj.ConfigObj')
@mock.patch('socket.socket', return_value=mock.MagicMock(name='socket', spec=socket.socket))
def test_read_from_zabbix(mock_socket, mock_configobj):
    """
    Test sending data to Zabbix Server
    """
    mock_configobj.side_effect = [
        {
            'LogFile': '/tmp/zabbix_agentd.log',
            'Server': '127.0.0.1',
            'ServerActive': '127.0.0.1',
            'Hostname': 'Zabbix server',
            'TLSConnect': 'cert',
            'TLSCAFile': '/tmp/tls_ca_file.crt',
            'TLSCertFile': '/tmp/tls_cert_file.crt',
            'TLSKeyFile': '/tmp/tls_key_file.key'
        }
    ]
    answer_payload = '{"info": "processed: 0; failed: 1; total: 1; seconds spent: 0.000441", "response": "success"}'
    answer_packet = b('ZBXD\1') + struct.pack('<Q', 93) + b(answer_payload)
    mock_socket.recv.return_value = answer_packet
    answer_awaited = json.loads(answer_payload)

    zbx_senderprotocol = protobix.SenderProtocol()
    zbx_senderprotocol.data_type='item'
    zbx_senderprotocol.socket = mock_socket
    result = zbx_senderprotocol._read_from_zabbix()
    assert result == answer_awaited

#@mock.patch('configobj.ConfigObj')
#@mock.patch('socket.socket', return_value=mock.MagicMock(name='socket', spec=socket.socket))
#@mock.patch('ssl.SSLContext', return_value=mock.MagicMock(name='ssl.SSLContext', spec=ssl.SSLContext))
#@mock.patch('protobix.ZabbixAgentConfig', return_value=mock.MagicMock(name='protobix.ZabbixAgentConfig', spec=protobix.ZabbixAgentConfig))
#def test_init_ssl(mock_zabbix_agent_config,
#                  mock_ssl_context,
#                  mock_socket,
#                  mock_configobj):
#    """
#    Test SSL context initialization
#    """
#    mock_configobj.side_effect = [
#        {
#            'TLSConnect': 'cert',
#            'TLSCAFile': '/tmp/tls_ca_file.crt',
#            'TLSCertFile': '/tmp/tls_cert_file.crt',
#            'TLSKeyFile': '/tmp/tls_cert_file.key'
#        }
#    ]
#    mock_zabbix_agent_config.tls_connect = 'cert'
#    mock_zabbix_agent_config.tls_cert_file.return_value = '/tmp/tls_cert_file.crt'
#    mock_zabbix_agent_config.tls_key_file.return_value = '/tmp/tls_cert_file.key'
#    zbx_senderprotocol = protobix.SenderProtocol()
#    print(zbx_senderprotocol._config)
#    #zbx_senderprotocol.socket = mock_socket
#    ssl_context = zbx_senderprotocol._init_ssl()
#    mock_ssl_context.assert_called_with(ssl.PROTOCOL_TLSv1_2)
#    mock_ssl_context.load_cert_chain.assert_called_with(
#        '/tmp/tls_cert_file.crt',
#        '/tmp/tls_cert_file.key'
#    )
#
#    assert ssl_context is None
