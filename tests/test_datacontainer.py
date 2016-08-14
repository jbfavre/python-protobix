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
def test_invalid_logger():
    """
    Adding data before assigning data_type should raise an Exception
    """
    with pytest.raises(ValueError) as err:
        zbx_datacontainer = protobix.DataContainer(logger='invalid')
    assert str(err.value) == 'logger requires a logging instance'

@pytest.mark.parametrize('data_type', pytest_params)
def test_items_add_before_set_data_type(data_type):
    """
    Adding data before assigning data_type should raise an Exception
    """
    zbx_datacontainer = protobix.DataContainer()
    assert zbx_datacontainer.items_list == []
    with pytest.raises(ValueError):
        zbx_datacontainer.add(DATA[data_type])
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.data_type = data_type
    zbx_datacontainer.add(DATA)
    assert len(zbx_datacontainer.items_list) == 4

@pytest.mark.parametrize('data_type', pytest_params)
def test_debug_no_dryrun_yes(data_type):
    """
    debug_level to False
    dryrun to True
    """
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.data_type = data_type
    zbx_datacontainer.dryrun = True
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA[data_type])
    assert len(zbx_datacontainer.items_list) == 4

    assert zbx_datacontainer.dryrun is True
    assert zbx_datacontainer.debug_level < 4

    ''' Send data to zabbix '''
    processed, failed, total, time = zbx_datacontainer.send()
    assert processed == -1
    assert failed == -1
    assert total == 4
    assert zbx_datacontainer.items_list == []

@pytest.mark.parametrize('data_type', pytest_params)
def test_debug_yes_dryrun_yes(data_type):
    """
    debug_level to True
    dryrun to True
    """
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.data_type = data_type
    zbx_datacontainer.dryrun = True
    zbx_datacontainer.debug_level = 4

    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA[data_type])

    assert len(zbx_datacontainer.items_list) == 4

    ''' Send data to zabbix '''
    processed, failed, total, time = zbx_datacontainer.send()
    assert processed == -4
    assert failed == -4
    assert total == 4
    assert zbx_datacontainer.items_list == []

@pytest.mark.parametrize('data_type', pytest_params)
def test_debug_no_dryrun_no(data_type):
    """
    debug_level to False
    dryrun to False
    """
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
def test_debug_yes_dryrun_no(data_type):
    """
    debug_level to True
    dryrun to False
    """
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
def test_need_backend_debug_no_dryrun_no(data_type):
    """
    debug_level to False
    dryrun to False
    """
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.data_type = data_type
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA[data_type])
    assert len(zbx_datacontainer.items_list) == 4

    assert zbx_datacontainer.dryrun is False
    assert zbx_datacontainer.debug_level < 4

    ''' Send data to zabbix '''
    processed, failed, total, time = zbx_datacontainer.send()
    assert processed == 4
    assert failed == 0
    assert total == 4
    assert zbx_datacontainer.items_list == []

@pytest.mark.parametrize('data_type', pytest_params)
def test_need_backend_debug_yes_dryrun_no(data_type):
    """
    debug_level to True
    dryrun to False
    """
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.debug_level = 4
    zbx_datacontainer.data_type = data_type
    assert zbx_datacontainer.items_list == []
    zbx_datacontainer.add(DATA[data_type])
    assert len(zbx_datacontainer.items_list) == 4

    assert zbx_datacontainer.dryrun is False
    assert zbx_datacontainer.debug_level >= 4

    ''' Send data to zabbix '''
    processed, failed, total, time = zbx_datacontainer.send()
    assert processed == 4
    assert failed == 0
    assert total == 4
    assert zbx_datacontainer.items_list == []

@pytest.mark.parametrize('data_type', pytest_params)
def test_server_connection_fails(data_type):
    """
    Connection to Zabbix Server fails
    """
    zbx_datacontainer = protobix.DataContainer()
    zbx_datacontainer.server_port = 10060
    zbx_datacontainer.data_type = data_type
    assert zbx_datacontainer.items_list == []
    assert zbx_datacontainer.server_port == 10060
    zbx_datacontainer.add(DATA[data_type])
    with pytest.raises(IOError):
        zbx_datacontainer.send()
    assert zbx_datacontainer.items_list == []
