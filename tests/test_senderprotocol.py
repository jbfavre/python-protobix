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

def test_default_params():
    """
    Default configuration
    """
    zbx_senderprotocol = protobix.SenderProtocol()

    assert zbx_senderprotocol.server_active == '127.0.0.1'
    assert zbx_senderprotocol.server_port == 10051
    assert zbx_senderprotocol._config.dryrun is False
    assert zbx_senderprotocol.items_list == []

def test_server_active_custom():
    """
    Test setting zbx_server with custom value
    """
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.server_active == '127.0.0.1'
    zbx_senderprotocol.server_active = 'myserver.domain.tld'
    assert zbx_senderprotocol.server_active == 'myserver.domain.tld'

def test_server_port_custom():
    """
    Test setting server_port with custom value
    """
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.server_port == 10051
    zbx_senderprotocol.server_port = 10052
    assert zbx_senderprotocol.server_port == 10052

def test_server_port_invalid_greater_than_32767():
    """
    Test setting server_port with invalid value
    """
    zbx_senderprotocol = protobix.SenderProtocol()
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol.server_port = 40000
    assert str(err.value) == 'ServerPort must be between 1024 and 32767'
    assert zbx_senderprotocol.server_port == 10051

def test_server_port_invalid_lower_than_1024():
    """
    Test setting server_port with invalid value
    """
    zbx_senderprotocol = protobix.SenderProtocol()
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol.server_port = 1000
    assert str(err.value) == 'ServerPort must be between 1024 and 32767'
    assert zbx_senderprotocol.server_port == 10051

def test_debug_custom():
    """
    Test setting server_port with custom value
    """
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.debug_level == 3
    zbx_senderprotocol.debug_level = 4
    assert zbx_senderprotocol.debug_level == 4

def test_debug_invalid_lower_than_0():
    """
    Test setting server_port with invalid value
    """
    zbx_senderprotocol = protobix.SenderProtocol()
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol.debug_level = -1
    assert str(err.value) == 'DebugLevel must be between 0 and 5, -1 provided'
    assert zbx_senderprotocol.debug_level == 3

def test_debug_invalid_greater_than_5():
    """
    Test setting server_port with invalid value
    """
    zbx_senderprotocol = protobix.SenderProtocol()
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol.debug_level = 10
    assert str(err.value) == 'DebugLevel must be between 0 and 5, 10 provided'
    assert zbx_senderprotocol.debug_level == 3

def test_dryrun_custom():
    """
    Test setting dryrun with custom value
    """
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol._config.dryrun is False
    zbx_senderprotocol._config.dryrun = True
    assert zbx_senderprotocol._config.dryrun is True
    zbx_senderprotocol._config.dryrun = False
    assert zbx_senderprotocol._config.dryrun is False

def test_dryrun_invalid():
    """
    Test setting dryrun with invalid value
    """
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol._config.dryrun is False
    with pytest.raises(ValueError) as err:
        zbx_senderprotocol._config.dryrun = 'invalid'
    assert str(err.value) == 'dryrun parameter requires boolean'
    assert zbx_senderprotocol._config.dryrun is False

def test_clock_integer():
    """
    Test clock method
    """
    zbx_senderprotocol = protobix.SenderProtocol()
    assert isinstance(zbx_senderprotocol.clock, int) is True

def test_clock_accurate():
    """
    Test clock method
    """
    zbx_senderprotocol = protobix.SenderProtocol()
    assert zbx_senderprotocol.clock == int(time.time())

@mock.patch('socket.socket', return_value=mock.MagicMock(name='socket', spec=socket.socket))
def test_send_to_zabbix(mock_socket):
    """
    Test sending data to Zabbix Server
    """
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

def test_send_to_zabbix_dryrun():
    """
    Test sending data to Zabbix Server
    """
    zbx_senderprotocol = protobix.SenderProtocol()
    zbx_senderprotocol.data_type='item'
    zbx_senderprotocol._config.dryrun = True
    result = zbx_senderprotocol._send_to_zabbix(zbx_senderprotocol._items_list)
    assert result == 0

@mock.patch('socket.socket', return_value=mock.MagicMock(name='socket', spec=socket.socket))
def test_read_from_zabbix(mock_socket):
    """
    Test sending data to Zabbix Server
    """
    answer_payload = '{"info": "processed: 0; failed: 1; total: 1; seconds spent: 0.000441", "response": "success"}'
    answer_packet = b('ZBXD\1') + struct.pack('<Q', 93) + b(answer_payload)
    mock_socket.recv.return_value = answer_packet
    answer_awaited = json.loads(answer_payload)

    zbx_senderprotocol = protobix.SenderProtocol()
    zbx_senderprotocol.data_type='item'
    zbx_senderprotocol.socket = mock_socket
    result = zbx_senderprotocol._read_from_zabbix()
    assert result == answer_awaited

@mock.patch('socket.socket', return_value=mock.MagicMock(name='socket', spec=socket.socket))
def test_read_from_zabbix(mock_socket):
    """
    Test sending data to Zabbix Server
    """
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
def test_init_tls(mock_configobj):
    """
    Test TLS context initialization
    """
    mock_configobj.side_effect = [
        {
            'TLSConnect': 'cert',
            'TLSCAFile': '/tmp/tls_cert_file.pem',
            'TLSCertFile': '/tmp/tls_cert_file.pem',
            'TLSKeyFile': '/tmp/tls_key_file.pem'
        }
    ]
    zbx_senderprotocol = protobix.SenderProtocol()
    with pytest.raises(IOError) as err:
        tls_context = zbx_senderprotocol._init_tls()
    #assert isinstance(tls_context, ssl.SSLContext)

#@mock.patch('configobj.ConfigObj')
#def test_init_tls_no_tls(mock_configobj):
#    """
#    Test SSL context initialization
#    """
#    mock_configobj.side_effect = [
#        {
#            'TLSConnect': 'unencrypted',
#        }
#    ]
#    zbx_senderprotocol = protobix.SenderProtocol()
#    _socket = zbx_senderprotocol._socket()
#    assert isinstance(_socket, socket.socket)
