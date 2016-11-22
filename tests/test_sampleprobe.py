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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import protobix
import logging
import argparse

# Zabbix force TLSv1.2 protocol
# in src/libs/zbxcrypto/tls.c function zbx_tls_init_child
HAVE_DECENT_SSL = False
if sys.version_info > (2,7,9):
    import ssl
    HAVE_DECENT_SSL = True

class ProtobixTestProbe(protobix.SampleProbe):
    __version__="1.0.0"

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

class ProtobixTLSTestProbe(ProtobixTestProbe):

    def run(self, options=None):
        # Init logging with default values since we don't have real config yet
        self._init_logging()
        # Parse command line options
        args = sys.argv[1:]
        if isinstance(options, list):
            args = options
        self.options = self._parse_args(args)

        # Get configuration
        self.zbx_config = self._init_config()

        # Update logger with configuration
        self._setup_logging(
            self.zbx_config.log_type,
            self.zbx_config.debug_level,
            self.zbx_config.log_file
        )

        # Datacontainer init
        zbx_container = protobix.DataContainer(
            config = self.zbx_config,
            logger=self.logger
        )
        # Get back hostname from ZabbixAgentConfig
        self.hostname = self.zbx_config.hostname

        # Step 1: read probe configuration
        #         initialize any needed object or connection
        self._init_probe()

        # Step 2: get data
        data = {}
        if self.options.probe_mode == "update":
            zbx_container.data_type = 'items'
            data = self._get_metrics()
        elif self.options.probe_mode == "discovery":
            zbx_container.data_type = 'lld'
            data = self._get_discovery()

        # Step 3: add data to container
        zbx_container.add(data)

        # Step 4: send data to Zabbix server
        server_success, server_failure, processed, failed, total, time = zbx_container.send()
        return  server_success, server_failure, processed, failed, total, time

class ProtobixTestProbe2(protobix.SampleProbe):
    __version__="1.0.0"

"""
Check default configuration of the sample probe
"""
def test_default_configuration():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args([])
    assert pbx_test_probe.options.config_file is None
    assert pbx_test_probe.options.debug_level is None
    assert pbx_test_probe.options.discovery is False
    assert pbx_test_probe.options.dryrun is False
    assert pbx_test_probe.options.update is False
    assert pbx_test_probe.options.server_port is None
    assert pbx_test_probe.options.server_active is None

"""
Check --update-items argument
"""
def test_command_line_option_update_items():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--update-items'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_test_probe.options.discovery is False
    assert pbx_test_probe.options.update is True
    assert pbx_test_probe.options.probe_mode == 'update'

"""
Check --discovery argument
"""
def test_command_line_option_discovery():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--discovery'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_test_probe.options.discovery is True
    assert pbx_test_probe.options.update is False
    assert pbx_test_probe.options.probe_mode == 'discovery'

"""
Check exception when providing both --update-items & --discovery arguments
"""
def test_force_both_discovery_and_update():
    pbx_test_probe = ProtobixTestProbe()
    with pytest.raises(ValueError):
      result = pbx_test_probe.run(['--discovery', '--update-items'])

"""
Check -v argument. Used to set logger log level
"""
def test_force_verbosity():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['-vvvv'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_test_probe.options.debug_level == 4
    pbx_test_probe.options = pbx_test_probe._parse_args(['-vv'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_test_probe.options.debug_level == 2
    pbx_test_probe.options = pbx_test_probe._parse_args(['-vvvvvvvvv'])
    assert pbx_test_probe.options.debug_level == 9
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.debug_level == 4

"""
Check -d & --dryrun argument.
"""
def test_force_dryrun():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--dryrun'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_test_probe.options.dryrun is True
    pbx_test_probe.options = pbx_test_probe._parse_args(['-d'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_test_probe.options.dryrun is True

"""
Check -z & --zabbix-server argument.
"""
def test_command_line_option_zabbix_server():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--zabbix-server', '192.168.0.1'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.server_active == '192.168.0.1'
    pbx_test_probe.options = pbx_test_probe._parse_args(['-z', '192.168.0.2'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.server_active == '192.168.0.2'

"""
Check -p & --port argument.
"""
def test_command_line_option_port():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--port', '10052'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.server_port == 10052
    pbx_test_probe.options = pbx_test_probe._parse_args(['-p', '10060'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.server_port == 10060

"""
Check --tls-cert-file argument.
"""
def test_command_line_option_tls_cert_file():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--tls-cert-file', '/tmp/test_file.crt'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.tls_cert_file == '/tmp/test_file.crt'

"""
Check --tls-key-file argument.
"""
def test_command_line_option_tls_key_file():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--tls-key-file', '/tmp/test_file.key'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.tls_key_file == '/tmp/test_file.key'

"""
Check --tls-ca-file argument.
"""
def test_command_line_option_tls_ca_file():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--tls-ca-file', '/tmp/test_ca_file.crt'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.tls_ca_file == '/tmp/test_ca_file.crt'

"""
Check --tls-crl-file argument.
"""
def test_command_line_option_tls_crl_file():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--tls-crl-file', '/tmp/test_file.crl'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.tls_crl_file == '/tmp/test_file.crl'

"""
Check --tls-psk-file argument.
"""
def test_command_line_option_tls_psk_file():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--tls-psk-file', '/tmp/test_file.psk'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.tls_psk_file == '/tmp/test_file.psk'

"""
Check --tls-psk-identity argument.
"""
def test_command_line_option_tls_psk_identity():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--tls-psk-identity', 'Zabbix TLS/PSK identity'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.tls_psk_identity == 'Zabbix TLS/PSK identity'

"""
Check --tls-server-cert-issuer argument.
"""
def test_command_line_option_tls_server_cert_issuer():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--tls-server-cert-issuer', 'Zabbix TLS cert issuer'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.tls_server_cert_issuer == 'Zabbix TLS cert issuer'

"""
Check --tls-server-cert-subject argument.
"""
def test_command_line_option_tls_server_cert_subject():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--tls-server-cert-subject', 'Zabbix TLS cert subject'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.tls_server_cert_subject == 'Zabbix TLS cert subject'

"""
Check --tls-connect argument.
"""
def test_command_line_option_tls_connect():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe.options = pbx_test_probe._parse_args(['--tls-connect', 'cert'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.tls_connect == 'cert'
    pbx_test_probe.options = pbx_test_probe._parse_args(['--tls-connect', 'psk'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.tls_connect == 'psk'
    pbx_test_probe.options = pbx_test_probe._parse_args(['--tls-connect', 'unencrypted'])
    pbx_config = pbx_test_probe._init_config()
    assert pbx_config.tls_connect == 'unencrypted'

"""
Check logger configuration in console mode
"""
def test_log_console():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe._init_logging()
    assert isinstance(pbx_test_probe.logger, logging.Logger)
    pbx_test_probe._setup_logging('console', 4, '/tmp/log_file')
    assert len(pbx_test_probe.logger.handlers) == 1
    assert pbx_test_probe.logger.level == logging.DEBUG
    assert isinstance(pbx_test_probe.logger.handlers[0], logging.StreamHandler)

"""
Check logger configuration in file mode & debug
"""
def test_log_file():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe._init_logging()
    assert isinstance(pbx_test_probe.logger, logging.Logger)
    pbx_test_probe._setup_logging('file', 4, '/tmp/log_file')
    assert len(pbx_test_probe.logger.handlers) == 1
    assert pbx_test_probe.logger.level == logging.DEBUG
    assert isinstance(pbx_test_probe.logger.handlers[0], logging.FileHandler)

"""
Check logger configuration in file mode with invalid file
Here, invalid means that it doesn't exists, or we don't have
permission to write into
"""
def test_log_file_invalid():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe._init_logging()
    assert isinstance(pbx_test_probe.logger, logging.Logger)
    with pytest.raises(IOError):
        pbx_test_probe._setup_logging('file', 4, '/do_not_have_permission')
    assert pbx_test_probe.logger.level == logging.NOTSET
    assert len(pbx_test_probe.logger.handlers) == 0

"""
Check logger configuration in system (syslog) mode
"""
def test_log_syslog():
    pbx_test_probe = ProtobixTestProbe()
    pbx_test_probe._init_logging()
    assert isinstance(pbx_test_probe.logger, logging.Logger)
    pbx_test_probe._setup_logging('system', 3, None)
    assert len(pbx_test_probe.logger.handlers) == 1
    assert pbx_test_probe.logger.level == logging.INFO
    assert isinstance(pbx_test_probe.logger.handlers[0], logging.handlers.SysLogHandler)

"""
Check a custom probe without _get_metrics method.
"""
def test_not_implemented_get_metrics():
    pbx_test_probe = ProtobixTestProbe2()
    with pytest.raises(NotImplementedError):
        pbx_test_probe.run([])

"""
Check a custom probe without _get_discovery method.
"""
def test_not_implemented_get_discovery():
    pbx_test_probe = ProtobixTestProbe2()
    with pytest.raises(NotImplementedError):
        pbx_test_probe.run(['--discovery'])

"""
Check that sample probe correctly catches exception from _init_probe
"""
def test_init_probe_exception():
    pbx_test_probe = ProtobixTestProbe2()
    with mock.patch('protobix.SampleProbe._init_probe') as mock_init_probe:
        mock_init_probe.side_effect = Exception('Something went wrong')
        result = pbx_test_probe.run([])
        assert result == 1

"""
Check that sample probe correctly catches exception from _get_metrics
"""
def test_get_metrics_exception():
    pbx_test_probe = ProtobixTestProbe2()
    with mock.patch('protobix.SampleProbe._get_metrics') as mock_get_metrics:
        mock_get_metrics.side_effect = Exception('Something went wrong in _get_metrics')
        result = pbx_test_probe.run([])
        assert result == 2

"""
Check that sample probe correctly catches exception from _get_discovery
"""
def test_get_discovery_exception():
    pbx_test_probe = ProtobixTestProbe2()
    with mock.patch('protobix.SampleProbe._get_discovery') as mock_get_discovery:
        mock_get_discovery.side_effect = Exception('Something went wrong in _get_discovery')
        result = pbx_test_probe.run(['--discovery'])
        assert result == 2

"""
Check that sample probe correctly catches exception from DataContainer add method
"""
def test_datacontainer_add_exception():
    pbx_test_probe = ProtobixTestProbe()
    with mock.patch('protobix.DataContainer.add') as mock_datacontainer_add:
        mock_datacontainer_add.side_effect = Exception('Something went wrong in DataContainer.add')
        result = pbx_test_probe.run([])
        assert result == 3

"""
Check that sample probe correctly catches exception from DataContainer send method
"""
def test_datacontainer_send_exception():
    pbx_test_probe = ProtobixTestProbe()
    with mock.patch('protobix.DataContainer.send') as mock_datacontainer_send:
        mock_datacontainer_send.side_effect = Exception('Another something went wrong')
        result = pbx_test_probe.run([])
        assert result == 4

"""
Check that sample probe correctly catches socket exception from DataContainer send method
"""
def test_datacontainer_send_socket_error():
    pbx_test_probe = ProtobixTestProbe()
    with mock.patch('protobix.DataContainer.send') as mock_datacontainer_send:
        mock_datacontainer_send.side_effect = socket.error
        result = pbx_test_probe.run([])
        assert result == 4

"""
Check return 0 when everything is fine
"""
def test_everything_runs_fine():
    pbx_test_probe = ProtobixTestProbe()
    with mock.patch('protobix.DataContainer.send') as mock_datacontainer_send:
        mock_datacontainer_send.side_effect = None
        result = pbx_test_probe.run([])
        assert result == 0

if HAVE_DECENT_SSL is True:

    """
    Check sending data with or without TLS with debug disabled
    """
    pytest_matrix = (
        ('items', False, False),
        ('lld', False, False),
        ('items', True, False),
        ('lld', True, False),
        ('items', False, True),
        ('lld', False, True),
        ('items', True, True),
        ('lld', True, True),
    )
    @pytest.mark.parametrize('data_type,tls_enabled,tls_crl_enabled', pytest_matrix)
    def test_need_backend_tls_cert(data_type, tls_enabled, tls_crl_enabled):
        params = []
        if tls_enabled:
            params = [
                '--tls-connect', 'cert',
                '--tls-ca-file', 'tests/tls_ca/rogue-protobix-ca.cert.pem',
                '--tls-cert-file', 'tests/tls_ca/rogue-protobix-client.cert.pem',
                '--tls-key-file', 'tests/tls_ca/rogue-protobix-client.key.pem',
            ]
        if tls_crl_enabled:
            params.append('--tls-crl-file')
            params.append('tests/tls_ca/rogue-protobix.crl')
        params.append('--update' if data_type == 'items' else '--discovery')
        params.append('-vvv')
        pbx_test_probe = ProtobixTLSTestProbe()
        server_success, server_failure, processed, failed, total, time = pbx_test_probe.run(params)
        if tls_enabled is False:
            assert server_success == 1
            assert server_failure == 0
            assert processed == 4
            assert failed == 0
            assert total == 4
        else:
            # protobix.host1 does NOT have TLS enabled
            # therefore items sent on behalf of protobix.host1 must fail
            assert server_success == 1
            assert server_failure == 0
            assert processed == 2
            assert failed == 2
            assert total == 4

    """
    Check sending data with or without TLS with debug enabled
    """
    pytest_matrix = (
        ('items', False, False),
        ('lld', False, False),
        ('items', True, False),
        ('lld', True, False),
        ('items', False, True),
        ('lld', False, True),
        ('items', True, True),
        ('lld', True, True),
    )
    @pytest.mark.parametrize('data_type,tls_enabled,tls_crl_enabled', pytest_matrix)
    def test_need_backend_tls_cert_debug(data_type, tls_enabled, tls_crl_enabled):
        params = []
        if tls_enabled:
            params = [
                '--tls-connect', 'cert',
                '--tls-ca-file', 'tests/tls_ca/rogue-protobix-ca.cert.pem',
                '--tls-cert-file', 'tests/tls_ca/rogue-protobix-client.cert.pem',
                '--tls-key-file', 'tests/tls_ca/rogue-protobix-client.key.pem',
            ]
        if tls_crl_enabled:
            params.append('--tls-crl-file')
            params.append('tests/tls_ca/rogue-protobix.crl')
        params.append('--update' if data_type == 'items' else '--discovery')
        params.append('-vvvvv')
        pbx_test_probe = ProtobixTLSTestProbe()
        server_success, server_failure, processed, failed, total, time = pbx_test_probe.run(params)
        if tls_enabled is False:
            assert server_success == 4
            assert server_failure == 0
            assert processed == 4
            assert failed == 0
            assert total == 4
        else:
            # protobix.host1 does NOT have TLS enabled
            # therefore items sent on behalf of protobix.host1 must fail
            assert server_success == 4
            assert server_failure == 0
            assert processed == 2
            assert failed == 2
            assert total == 4

    """
    Check sending data with or without TLS with debug disabled
    """
    pytest_matrix = (
        ('items', False, False),
        ('lld', False, False),
        ('items', True, False),
        ('lld', True, False),
        ('items', False, True),
        ('lld', False, True),
        ('items', True, True),
        ('lld', True, True),
    )
    @pytest.mark.parametrize('data_type,tls_enabled,tls_crl_enabled', pytest_matrix)
    def test_need_backend_tls_cert_invalid(data_type, tls_enabled, tls_crl_enabled):
        params = []
        if tls_enabled:
            params = [
                '--tls-connect', 'cert',
                '--tls-ca-file', 'tests/tls_ca/protobix-ca.cert.pem',
                '--tls-cert-file', 'tests/tls_ca/protobix-client.cert.pem',
                '--tls-key-file', 'tests/tls_ca/protobix-client.key.pem',
            ]
        if tls_crl_enabled:
            params.append('--tls-crl-file')
            params.append('tests/tls_ca/protobix.crl')
        params.append('--update' if data_type == 'items' else '--discovery')
        params.append('-vvv')
        pbx_test_probe = ProtobixTLSTestProbe()
        if tls_enabled is True:
            with pytest.raises(ssl.SSLError) as err:
                pbx_test_probe.run(params)
        else:
            server_success, server_failure, processed, failed, total, time = pbx_test_probe.run(params)
            assert server_success == 1
            assert server_failure == 0
            assert processed == 4
            assert failed == 0
            assert total == 4

    """
    Check sending data with or without TLS with debug enabled
    """
    pytest_matrix = (
        ('items', False, False),
        ('lld', False, False),
        ('items', True, False),
        ('lld', True, False),
        ('items', False, True),
        ('lld', False, True),
        ('items', True, True),
        ('lld', True, True),
    )
    @pytest.mark.parametrize('data_type,tls_enabled,tls_crl_enabled', pytest_matrix)
    def test_need_backend_tls_cert_invalid_debug(data_type, tls_enabled, tls_crl_enabled):
        params = []
        if tls_enabled:
            params = [
                '--tls-connect', 'cert',
                '--tls-ca-file', 'tests/tls_ca/protobix-ca.cert.pem',
                '--tls-cert-file', 'tests/tls_ca/protobix-client.cert.pem',
                '--tls-key-file', 'tests/tls_ca/protobix-client.key.pem',
            ]
        if tls_crl_enabled:
            params.append('--tls-crl-file')
            params.append('tests/tls_ca/protobix.crl')
        params.append('--update' if data_type == 'items' else '--discovery')
        params.append('-vvvvv')
        pbx_test_probe = ProtobixTLSTestProbe()
        if tls_enabled is True:
            with pytest.raises(ssl.SSLError) as err:
                pbx_test_probe.run(params)
        else:
            server_success, server_failure, processed, failed, total, time = pbx_test_probe.run(params)
            assert server_success == 4
            assert server_failure == 0
            assert processed == 4
            assert failed == 0
            assert total == 4
