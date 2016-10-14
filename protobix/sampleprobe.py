import argparse
from argparse import RawTextHelpFormatter
import socket
import sys
import traceback
import logging
from logging import handlers

from .datacontainer import DataContainer
from .zabbixagentconfig import ZabbixAgentConfig

class SampleProbe(object):

    __version__ = '1.0.0rc1'
    # Mapping between zabbix-agent Debug option & logging level
    LOG_LEVEL = [
        logging.NOTSET,
        logging.CRITICAL,
        logging.ERROR,
        logging.INFO,
        logging.DEBUG,
        logging.DEBUG,
    ]
    logger = None
    probe_config = None
    hostname = None
    options = None

    def _parse_args(self, args):
        if self.logger:
            self.logger.info(
                "Read command line options"
            )
        # Parse the script arguments
        parser = argparse.ArgumentParser(
            usage='%(prog)s [options]',
            formatter_class=RawTextHelpFormatter,
            epilog='Protobix - copyright 2016 - Jean Baptiste Favre (www.jbfavre.org)'
        )
        # Probe operation mode
        probe_mode = parser.add_argument_group('Probe commands')
        probe_mode.add_argument(
            '--update-items', action='store_true', dest='update',
            help="Get & send items to Zabbix.\nThis is the default behaviour"
        )
        probe_mode.add_argument(
            '--discovery', action='store_true',
            help="If specified, will perform Zabbix Low Level Discovery."
        )
        # Common options
        common = parser.add_argument_group('Common options')
        common.add_argument(
            '-d', '--dryrun', action='store_true',
            help="Do not send anything to Zabbix. Usefull to debug with\n"
                 "--verbose option"
        )
        common.add_argument(
            '-v', action='count', dest='debug_level',
            help="Enable verbose mode. Is used to setup logging level.\n"
                 "Specifying 4 or more 'v' (-vvvv) enables Debug. Items are then\n"
                 "sent one after the other instead of bulk"
        )
        # Protobix specific options
        protobix = parser.add_argument_group('Protobix specific options')
        protobix.add_argument(
            '-z', '--zabbix-server', dest='server_active',
            help="Hostname or IP address of Zabbix server. If a host is\n"
                 "monitored by a proxy, proxy hostname or IP address\n"
                 "should be used instead. When used together with\n"
                 "--config, overrides the first entry of ServerActive\n"
                 "parameter specified in agentd configuration file."
        )
        protobix.add_argument(
            '-p', '--port', dest='server_port',
            help="Specify port number of Zabbix server trapper running on\n"
                 "the server. Default is 10051. When used together with \n"
                 "--config, overrides the port of first entry of\n"
                 "ServerActive parameter specified in agentd configuration\n"
                 "file."
        )
        protobix.add_argument(
            '-c', '--config', dest='config_file',
            help="Use config-file. Zabbix sender reads server details from\n"
                 "the agentd configuration file. By default Protobix reads\n"
                 "`/etc/zabbix/zabbix_agentd.conf`.\n"
                 "Absolute path should be specified."
        )
        protobix.add_argument(
            '--tls-connect', choices=['unencrypted', 'psk', 'cert'],
            help="How to connect to server or proxy. Values:\n"
                 "unencrypted connect without encryption\n"
                 "psk connect using TLS and a pre-shared key\n"
                 "cert connect using TLS and a certificate."
        )
        protobix.add_argument(
            '--tls-ca-file',
            help="Full pathname of a file containing the top-level CA(s)\n"
                 "certificates for peer certificate verification."
        )
        protobix.add_argument(
            '--tls-cert-file',
            help="Full pathname of a file containing the certificate or\n"
                 "certificate chain."
        )
        protobix.add_argument(
            '--tls-key-file',
            help="Full pathname of a file containing the private key."
        )
        protobix.add_argument(
            '--tls-crl-file',
            help="Full pathname of a file containing revoked certificates."
        )
        protobix.add_argument(
            '--tls-server-cert-issuer',
            help="Allowed server certificate issuer."
        )
        protobix.add_argument(
            '--tls-server-cert-subject',
            help="Allowed server certificate subject."
        )
        # TLS PSK is not implemented in Python
        # https://bugs.python.org/issue19084
        # Following options are not implemented
        protobix.add_argument(
            '--tls-psk-identity',
            help="PSK-identity string."
        )
        protobix.add_argument(
            '--tls-psk-file',
            help="Full pathname of a file containing the pre-shared key."
        )
        # Probe specific options
        parser = self._parse_probe_args(parser)
        # Analyze provided command line options
        options = parser.parse_args(args)

        # Check that we don't have both '--update' & '--discovery' options
        options.probe_mode = 'update'
        if options.update is True and options.discovery is True:
            raise ValueError(
                'You can\' use both --update-items & --discovery options'
            )
        elif options.discovery is True:
            options.probe_mode = 'discovery'

        return options

    def _init_logging(self):
        logger = logging.getLogger(self.__class__.__name__)
        logger.handlers = []
        logger.setLevel(logging.NOTSET)
        self.logger = logger

    def _setup_logging(self, log_type, debug_level, log_file):
        if self.logger:
            self.logger.info(
                "Initialize logging"
            )
        # Enable log like Zabbix Agent does
        # Though, when we have a tty, it's convenient to use console to log
        common_log_format = '[%(name)s:%(levelname)s] %(message)s'
        if log_type == 'console' or sys.stdout.isatty():
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                fmt=common_log_format,
                datefmt='%Y%m%d:%H%M%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        if log_type == 'file':
            file_handler = logging.FileHandler(log_file)
            # Use same date format as Zabbix: when logging into
            # zabbix_agentd log file, it's easier to read & parse
            log_formatter = logging.Formatter(
                fmt='%(process)d:%(asctime)s.%(msecs)03d ' + common_log_format,
                datefmt='%Y%m%d:%H%M%S'
            )
            file_handler.setFormatter(log_formatter)
            self.logger.addHandler(file_handler)
        if log_type == 'system':
            # TODO: manage syslog address as command line option
            syslog_handler = logging.handlers.SysLogHandler(
                address=('localhost', 514),
                facility=logging.handlers.SysLogHandler.LOG_DAEMON
            )
            # Use same date format as Zabbix does: when logging into
            # zabbix_agentd log file, it's easier to read & parse
            log_formatter = logging.Formatter(
                fmt='%(process)d:%(asctime)s.%(msecs)03d ' + common_log_format,
                datefmt='%Y%m%d:%H%M%S'
            )
            syslog_handler.setFormatter(log_formatter)
            self.logger.addHandler(syslog_handler)
        self.logger.setLevel(
            self.LOG_LEVEL[debug_level]
        )

    def _init_config(self):
        if self.logger:
            self.logger.info(
                "Get configuration"
            )
        # Get config from ZabbixAgentConfig
        zbx_config = ZabbixAgentConfig(self.options.config_file)

        # And override it with provided command line options
        if self.options.server_active:
            zbx_config.server_active = self.options.server_active

        if self.options.server_port:
            zbx_config.server_port = int(self.options.server_port)

        # tls_connect 'cert' needed options
        if self.options.tls_cert_file:
            zbx_config.tls_cert_file = self.options.tls_cert_file

        if self.options.tls_key_file:
            zbx_config.tls_key_file = self.options.tls_key_file

        if self.options.tls_ca_file:
            zbx_config.tls_ca_file = self.options.tls_ca_file

        if self.options.tls_crl_file:
            zbx_config.tls_crl_file = self.options.tls_crl_file

        # tls_connect 'psk' needed options
        if self.options.tls_psk_file:
            zbx_config.tls_psk_file = self.options.tls_psk_file

        if self.options.tls_psk_identity:
            zbx_config.tls_psk_identity = self.options.tls_psk_identity

        if self.options.tls_server_cert_issuer:
            zbx_config.tls_server_cert_issuer = self.options.tls_server_cert_issuer

        if self.options.tls_server_cert_subject:
            zbx_config.tls_server_cert_subject = self.options.tls_server_cert_subject

        # Set tls_connect last because it'll check above options
        # to ensure a coherent config set
        if self.options.tls_connect:
            zbx_config.tls_connect = self.options.tls_connect

        if self.options.debug_level:
            self.options.debug_level = min(4, self.options.debug_level)
            zbx_config.debug_level = self.options.debug_level

        zbx_config.dryrun = False
        if self.options.dryrun:
            zbx_config.dryrun = self.options.dryrun

        return zbx_config

    def _get_metrics(self):
        # mandatory method
        raise NotImplementedError

    def _get_discovery(self):
        # mandatory method
        raise NotImplementedError

    def _init_probe(self):
        # non mandatory method
        pass

    def _parse_probe_args(self, parser):
        # non mandatory method
        return parser

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
        zbx_container = DataContainer(
            config = self.zbx_config,
            logger=self.logger
        )
        # Get back hostname from ZabbixAgentConfig
        self.hostname = self.zbx_config.hostname

        # Step 1: read probe configuration
        #         initialize any needed object or connection
        try:
            self._init_probe()
        except:
            if self.logger:
                self.logger.critical(
                    "Step 1 - Read probe configuration failed"
                )
            self.logger.debug(traceback.format_exc())
            return 1

        # Step 2: get data
        try:
            data = {}
            if self.options.probe_mode == "update":
                zbx_container.data_type = 'items'
                data = self._get_metrics()
            elif self.options.probe_mode == "discovery":
                zbx_container.data_type = 'lld'
                data = self._get_discovery()
        except NotImplementedError as e:
            if self.logger:
                self.logger.critical(
                    "Step 2 - Get Data failed [%s]" % str(e)
                )
                self.logger.debug(traceback.format_exc())
            raise
        except Exception as e:
            if self.logger:
                self.logger.critical(
                    "Step 2 - Get Data failed [%s]" % str(e)
                )
                self.logger.debug(traceback.format_exc())
            return 2

        # Step 3: add data to container
        try:
            zbx_container.add(data)
        except Exception as e:
            if self.logger:
                self.logger.critical(
                    "Step 3 - Format & add Data failed [%s]" % str(e)
                )
                self.logger.debug(traceback.format_exc())
            zbx_container._reset()
            return 3

        # Step 4: send data to Zabbix server
        try:
            zbx_container.send()
        except socket.error as e:
            if self.logger:
                self.logger.critical(
                    "Step 4 - Sent to Zabbix Server [%s] failed [%s]" % (
                        self.zbx_config.server_active,
                        str(e)
                    )
                )
                self.logger.debug(traceback.format_exc())
            return 4
        except Exception as e:
            if self.logger:
                self.logger.critical(
                    "Step 4 - Unknown error [%s]" % str(e)
                )
                self.logger.debug(traceback.format_exc())
            return 4
        # Everything went fine. Let's return 0 and exit
        return 0
