import argparse
from argparse import RawTextHelpFormatter
import socket
import sys
import traceback
import logging
from logging import handlers

from .datacontainer import DataContainer

class SampleProbe(object):

    __version__ = '0.2.0'
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
        # Parse the script arguments
        parser = argparse.ArgumentParser(
            usage='%(prog)s [options]',
            formatter_class=RawTextHelpFormatter,
            description='A Protobix probe to monitor XXX with Zabbix',
            epilog='Protobix - copyright 2016 - Jean Baptiste Favre (www.jbfavre.org)'
        )
        # Probe operation mode
        probe_mode = parser.add_argument_group('Probe commands')
        probe_mode.add_argument(
            '--update-items', action='store_true',
            dest='update', default=False,
            help="Get & send items to Zabbix.\n"
                 "This is the default behaviour"
        )
        probe_mode.add_argument(
            '--discovery', action='store_true',
            dest='discovery', default=False,
            help="If specified, will perform Zabbix Low Level Discovery."
        )
        # Common options
        common = parser.add_argument_group('Common options')
        common.add_argument(
            '-d', '--dryrun', action='store_true', default=False,
            help="Do not send anything to Zabbix. Usefull to debug with\n"
                 "--verbose option"
        )
        common.add_argument(
            '-v', action='count', default=0, dest='debug_level',
            help="Enable verbose mode. Is used to setup logging level.\n"
                 "Specifying 4 or more 'v' (-vvvv) enables Debug. Items are then\n"
                 "sent one after the other instead of bulk"
        )
        # Protobix specific options
        protobix = parser.add_argument_group('Protobix specific options')
        protobix.add_argument(
            '-z', '--zabbix-server', default='127.0.0.1',
            help="Hostname or IP address of Zabbix server. If a host is\n"
                 "monitored by a proxy, proxy hostname or IP address\n"
                 "should be used instead. When used together with\n"
                 "--config, overrides the first entry of ServerActive\n"
                 "parameter specified in agentd configuration file."
        )
        protobix.add_argument(
            '-p', '--zabbix-port', default=10051, type=int,
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
        return parser.parse_args(args)

    def _setup_logging(self, log_type, debug_level, log_file):
        logger = logging.getLogger(self.__class__.__name__)
        logger.handlers = []
        common_log_format = '[%(name)s:%(levelname)s] %(message)s'
        # Enable log like Zabbix Agent does
        # Though, when we have a tty, it's convenient to use console to log
        if log_type == 'console' or sys.stdout.isatty():
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                fmt=common_log_format,
                datefmt='%Y%m%d:%H%M%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        if log_type == 'file':
            file_handler = logging.FileHandler(log_file)
            # Use same date format as Zabbix: when logging into
            # zabbix_agentd log file, it's easier to read & parse
            log_formatter = logging.Formatter(
                fmt='%(process)d:%(asctime)s.%(msecs)03d ' + common_log_format,
                datefmt='%Y%m%d:%H%M%S'
            )
            file_handler.setFormatter(log_formatter)
            logger.addHandler(file_handler)
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
            logger.addHandler(syslog_handler)
        logger.setLevel(
            self.LOG_LEVEL[debug_level]
        )
        return logger

    def _init_container(self):
        zbx_container = DataContainer(
            zbx_file=self.options.config_file,
            zbx_host=self.options.zabbix_server,
            zbx_port=int(self.options.zabbix_port),
            debug_level=self.options.debug_level,
            dryrun=self.options.dryrun,
            logger=self.logger
        )
        return zbx_container

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
        # Parse command line options
        args = sys.argv[1:]
        if isinstance(options, list):
            args = options
        self.options = self._parse_args(args)
        self.options.debug_level = min([4, self.options.debug_level])
        self.options.probe_mode = 'update'
        if self.options.update is True and self.options.discovery is True:
            raise ValueError(
                'You can\' use both --update-items & --discovery options'
            )
        elif self.options.discovery is True:
            self.options.probe_mode = 'discovery'

        # Datacontainer init
        zbx_container = self._init_container()
        # Get back hostname from DataContainer
        self.hostname = zbx_container.hostname

        # logger init
        # we need Zabbix configuration to know how to log
        self.logger = self._setup_logging(
            zbx_container.log_type,
            zbx_container.debug_level,
            zbx_container.log_file
        )
        zbx_container.logger = self.logger

        # Step 1: read probe configuration
        #         initialize any needed object or connection
        try:
            self._init_probe()
        except:
            self.logger.error(
                'Step 1 - Read probe configuration failed'
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
            self.logger.error(
                'Step 2 - Get Data failed [%s]' % str(e)
            )
            self.logger.debug(traceback.format_exc())
            raise
        except Exception as e:
            self.logger.error(
                'Step 2 - Get Data failed [%s]' % str(e)
            )
            self.logger.debug(traceback.format_exc())
            return 2

        # Step 3: add data to container
        try:
            zbx_container.add(data)
        except Exception as e:
            self.logger.error(
                'Step 3 - Format & add Data failed [%s]' % str(e)
            )
            self.logger.debug(traceback.format_exc())
            zbx_container._reset()
            return 3

        # Step 4: send data to Zabbix server
        try:
            zbx_container.send()
        except socket.error as e:
            self.logger.error(
                'Step 4 - Sent to Zabbix Server failed [%s]' % str(e)
            )
            self.logger.debug(traceback.format_exc())
            return 4
        except Exception as e:
            self.logger.error(
                'Step 4 - Unknown error [%s]' % str(e)
            )
            self.logger.debug(traceback.format_exc())
            return 4
        # Everything went fine. Let's return 0 and exit
        return 0
