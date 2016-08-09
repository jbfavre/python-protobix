"""
Test long running process & detect memory leak
"""
import configobj
import pytest
import mock
import unittest

import resource
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import protobix

PAYLOAD = {
    "items": {
        "protobix.host1": {
            "my.protobix.item.int": 0,
            "my.protobix.item.string": 1
        },
        "protobix.host2": {
            "my.protobix.item.int": 0,
            "my.protobix.item.string": 1
        },
        "protobix.host3": {
            "my.protobix.item.int": 0,
            "my.protobix.item.string": 1
        },
        "protobix.host4": {
            "my.protobix.item.int": 0,
            "my.protobix.item.string": 1
        },
        "protobix.host5": {
            "my.protobix.item.int": 0,
            "my.protobix.item.string": 1
        },
        "protobix.host6": {
            "my.protobix.item.int": 0,
            "my.protobix.item.string": 1
        },
        "protobix.host7": {
            "my.protobix.item.int": 0,
            "my.protobix.item.string": 1
        },
        "protobix.host8": {
            "my.protobix.item.int": 0,
            "my.protobix.item.string": 1
        }
    },
    "lld": {
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

def long_run(data_type, debug_level):
    """
    Generic long running process simulator
    Used by tests below
    """
    zbx_container = protobix.DataContainer(
        debug_level = debug_level,
    )
    run=1
    max_run=1000
    while run <= max_run:
        zbx_container.data_type = data_type
        zbx_container.add(PAYLOAD[data_type])
        try:
            zbx_container.send()
        except:
            pass
        if run % (max_run/10) == 0 or run <=1:
            usage=resource.getrusage(resource.RUSAGE_SELF)
            display_memory = usage[2]*resource.getpagesize()/1000000.0
            if run == 1:
                initial_memory = usage[2]
                display_initial_memory = usage[2]*resource.getpagesize()/1000000.0
            final_memory = usage[2]
            print ('Run %i: ru_maxrss=%f mb - initial=%f mb' % (
                run, (display_memory), display_initial_memory
            ))
        run += 1
    return initial_memory, final_memory

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_items_long_run_debug_no(mock_configobj, mock_zabbix_agent_config):
    """
    Simulate long running process without debug
    and control memory usage
    """
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    initial_memory, final_memory = long_run('items', 2)
    assert initial_memory == final_memory

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_items_long_run_debug_yes(mock_configobj, mock_zabbix_agent_config):
    """
    Simulate long running process in debug mode
    and control memory usage
    """
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    initial_memory, final_memory = long_run('items', 4)
    assert initial_memory == final_memory

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_lld_long_run_debug_no(mock_configobj, mock_zabbix_agent_config):
    """
    Simulate long running process without debug
    and control memory usage
    """
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    initial_memory, final_memory = long_run('lld', 2)
    assert initial_memory == final_memory

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_lld_long_run_debug_yes(mock_configobj, mock_zabbix_agent_config):
    """
    Simulate long running process in debug mode
    and control memory usage
    """
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    initial_memory, final_memory = long_run('lld', 4)
    assert initial_memory == final_memory
