"""
Test Protobix sampleprobe
"""
import configobj
import pytest
import mock
import unittest
import socket

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

def test_default_configuration():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args([])
    assert pbx_test_probe.options.config_file is None
    assert pbx_test_probe.options.debug is False
    assert pbx_test_probe.options.discovery is False
    assert pbx_test_probe.options.dryrun is False
    assert pbx_test_probe.options.update is False
    assert pbx_test_probe.options.zabbix_port == 10051
    assert pbx_test_probe.options.zabbix_server == '127.0.0.1'

def test_force_update():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--update-items'])
    assert pbx_test_probe.options.discovery is False
    assert pbx_test_probe.options.update is True

def test_force_discovery():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--discovery'])
    assert pbx_test_probe.options.discovery is True
    assert pbx_test_probe.options.update is False

def test_force_both_discovery_and_update():
    pbx_test_probe = ProtobixTestProbe()
    with pytest.raises(ValueError):
      result = pbx_test_probe.run(['--discovery', '--update-items'])

def test_force_debug():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--debug'])
    assert pbx_test_probe.options.debug is True
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['-D'])
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
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.run([])
    assert len(pbx_test_probe.logger.handlers) == 1
    assert isinstance(pbx_test_probe.logger.handlers[0], logging.StreamHandler)

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_log_file(mock_configobj, mock_zabbix_agent_config):
    mock_configobj.side_effect = [{ 'LogType': 'file' }]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.run([])
    assert len(pbx_test_probe.logger.handlers) == 1
    assert isinstance(pbx_test_probe.logger.handlers[0], logging.FileHandler)

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_log_file_invalid(mock_configobj, mock_zabbix_agent_config):
    mock_configobj.side_effect = [
        {
            'LogType': 'file',
            'LogFile': '/do_not_have_permission'
        }
    ]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    pbx_test_probe = ProtobixTestProbe()
    with pytest.raises(IOError):
        pbx_test_probe.run([])

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_log_syslog(mock_configobj, mock_zabbix_agent_config):
    mock_configobj.side_effect = [{ 'LogType': 'system' }]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.run([])
    assert len(pbx_test_probe.logger.handlers) == 1
    assert isinstance(pbx_test_probe.logger.handlers[0], logging.handlers.SysLogHandler)

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_not_implemented_get_metrics(mock_configobj, mock_zabbix_agent_config):
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    pbx_test_probe = ProtobixTestProbe2()
    with pytest.raises(NotImplementedError):
        pbx_test_probe.run([])

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_not_implemented_get_discovery(mock_configobj, mock_zabbix_agent_config):
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    pbx_test_probe = ProtobixTestProbe2()
    with pytest.raises(NotImplementedError):
        pbx_test_probe.run(['--discovery'])

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_init_probe_exception(mock_configobj, mock_zabbix_agent_config):
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    pbx_test_probe = ProtobixTestProbe2()
    with mock.patch('protobix.SampleProbe._init_probe') as mock_init_probe:
        mock_init_probe.side_effect = Exception('Something went wrong')
        result = pbx_test_probe.run([])
        assert result == 1

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_get_metrics_exception(mock_configobj, mock_zabbix_agent_config):
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    pbx_test_probe = ProtobixTestProbe2()
    with mock.patch('protobix.SampleProbe._get_metrics') as mock_get_metrics:
        mock_get_metrics.side_effect = Exception('Something went wrong')
        result = pbx_test_probe.run([])
        assert result == 2

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
def test_get_discovery_exception(mock_configobj, mock_zabbix_agent_config):
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    pbx_test_probe = ProtobixTestProbe2()
    with mock.patch('protobix.SampleProbe._get_discovery') as mock_get_discovery:
        mock_get_discovery.side_effect = Exception('Something went wrong')
        result = pbx_test_probe.run(['--discovery'])
        assert result == 2

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
@mock.patch('protobix.SampleProbe._get_metrics')
def test_datacontainer_add_exception(mock_configobj, mock_zabbix_agent_config, mock_get_metrics):
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    pbx_test_probe = ProtobixTestProbe2()
    mock_get_metrics.side_effect = None
    with mock.patch('protobix.DataContainer.add') as mock_datacontainer_add:
        mock_datacontainer_add.side_effect = Exception('Something went wrong')
        result = pbx_test_probe.run([])
        assert result == 3

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
@mock.patch('protobix.SampleProbe._get_metrics')
def test_datacontainer_send_exception(mock_configobj, mock_zabbix_agent_config, mock_get_metrics):
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    pbx_test_probe = ProtobixTestProbe2()
    mock_get_metrics.side_effect = None
    with mock.patch('protobix.DataContainer.send') as mock_datacontainer_send:
        mock_datacontainer_send.side_effect = Exception('Another something went wrong')
        result = pbx_test_probe.run([])
        assert result == 4

@mock.patch('configobj.ConfigObj')
@mock.patch('protobix.ZabbixAgentConfig')
@mock.patch('protobix.SampleProbe._get_metrics')
def test_datacontainer_send_socket_error(mock_configobj, mock_zabbix_agent_config, mock_get_metrics):
    mock_configobj.side_effect = [{}]
    mock_zabbix_agent_config.return_value = protobix.ZabbixAgentConfig()
    pbx_test_probe = ProtobixTestProbe2()
    mock_get_metrics.side_effect = None
    with mock.patch('protobix.DataContainer.send') as mock_datacontainer_send:
        mock_datacontainer_send.side_effect = socket.error
        result = pbx_test_probe.run([])
        assert result == 4
