"""
Test Protobix sampleprobe
"""
import configobj
import pytest
import mock
import unittest

import resource
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import protobix
import logging
import argparse

class ProtobixTestProbe(protobix.SampleProbe):
    __version__="0.1.2"

    def _get_metrics(self):
        return {
            "protobix.host1": {
                "my.protobix.item.int": 0,
                "my.protobix.item.string": "item string"
            },
            "protobix.host2": {
                "my.protobix.item.int": 0,
                "my.protobix.item.string": "item string"
            }
        }

    def _get_discovery(self):
        return {
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
class ProtobixTestProbe2(protobix.SampleProbe):
    __version__="0.1.2"

    def _parse_probe_args(self, parser):
        probe = parser.add_argument_group('Probe specific options')
        return parser

@mock.patch('configobj.ConfigObj')
def test_default_configuration(mock_configobj):
    #mock_datacontainer.return_value = protobix.DataContainer()
    pbx_test_probe = ProtobixTestProbe()
    result = pbx_test_probe.run([])
    assert result == 0
    assert pbx_test_probe.options.config_file is None
    assert pbx_test_probe.options.debug is False
    assert pbx_test_probe.options.discovery is False
    assert pbx_test_probe.options.dryrun is False
    assert pbx_test_probe.options.probe_mode == 'update'
    assert pbx_test_probe.options.update is False
    assert pbx_test_probe.options.zabbix_port == 10051
    assert pbx_test_probe.options.zabbix_server == '127.0.0.1'

def test_force_update():
    pbx_test_probe = ProtobixTestProbe()
    result = pbx_test_probe.run(['--update-items'])
    assert result == 0
    assert pbx_test_probe.options.discovery is False
    assert pbx_test_probe.options.probe_mode == 'update'
    assert pbx_test_probe.options.update is True

def test_force_discovery():
    pbx_test_probe = ProtobixTestProbe()
    result = pbx_test_probe.run(['--discovery'])
    assert result == 0
    assert pbx_test_probe.options.discovery is True
    assert pbx_test_probe.options.probe_mode == 'discovery'
    assert pbx_test_probe.options.update is False

def test_force_both_discovery_and_update():
    pbx_test_probe = ProtobixTestProbe()
    with pytest.raises(ValueError):
      result = pbx_test_probe.run(['--discovery', '--update-items'])

def test_force_debug():
    pbx_test_probe = ProtobixTestProbe()
    result = pbx_test_probe.run(['--debug'])
    assert result == 0
    assert pbx_test_probe.options.debug is True
    result = pbx_test_probe.run(['-D'])
    assert result == 0
    assert pbx_test_probe.options.debug is True

def test_force_dryrun():
    pbx_test_probe = ProtobixTestProbe()
    result = pbx_test_probe.run(['--dryrun'])
    assert result == 0
    assert pbx_test_probe.options.dryrun is True
    result = pbx_test_probe.run(['-d'])
    assert result == 0
    assert pbx_test_probe.options.dryrun is True

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_log_console(mock_configobj, mock_zabbix_agent_config):
    mock_configobj.side_effect = [{ 'LogType': 'console' }]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    with mock.patch('protobix.SampleProbe.logger', autospec=True) as mock_logging:
      pbx_test_probe = ProtobixTestProbe()
      result = pbx_test_probe.run(['--dryrun'])
      assert result == 0

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_log_console(mock_configobj, mock_zabbix_agent_config):
    mock_configobj.side_effect = [{ 'LogType': 'file' }]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    with mock.patch('protobix.SampleProbe.logger', autospec=True) as mock_logging:
      pbx_test_probe = ProtobixTestProbe()
      result = pbx_test_probe.run(['--dryrun'])
      assert result == 0

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_log_console(mock_configobj, mock_zabbix_agent_config):
    mock_configobj.side_effect = [{ 'LogType': 'system' }]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    with mock.patch('protobix.SampleProbe.logger', autospec=True) as mock_logging:
      pbx_test_probe = ProtobixTestProbe()
      result = pbx_test_probe.run(['--dryrun'])
      assert result == 0
