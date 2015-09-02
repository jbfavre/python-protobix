import logging
import optparse
import socket
import sys
import traceback
from logging import handlers

from .datacontainer import DataContainer

class SampleProbe(object):

    __version__ = '0.0.9'
    # Mapping between zabbix-agent Debug option & logging level
    LOG_LEVEL = [
        logging.NOTSET,
        logging.CRITICAL,
        logging.ERROR,
        logging.INFO,
        logging.DEBUG
    ]
    logger = None
    probe_config = None

    def _parse_args(self):
        # Parse the script arguments
        # Common part
        parser = optparse.OptionParser()

        parser.add_option('-c', '--config', default = None,
                          help='Probe config file location. '
                               'Can be either absolute or relative path')
        parser.add_option('-d', '--dry', action='store_true', default = False,
                          help='Performs CDH API calls but do not send '
                               'anything to the Zabbix server. Can be used '
                               'for both Update & Discovery mode')
        parser.add_option('-D', '--debug', action='store_true', default = False,
                          help='Enable debug mode. This will prevent bulk send '
                               'operations and force sending items one after the '
                               'other, displaying result for each one')

        zabbix_options = optparse.OptionGroup(parser, 'Zabbix configuration')
        zabbix_options.add_option('-z', '--zabbix-server', default='127.0.0.1',
                                  help='The hostname of Zabbix server or '
                                       'proxy, default is 127.0.0.1.')
        zabbix_options.add_option('-p', '--zabbix-port', default=10051,
                                  help='The port on which the Zabbix server or '
                                       'proxy is running, default is 10051.')
        zabbix_options.add_option('--update-items', action='store_const',
                                  dest='mode', const='update_items',
                                  help='Get & send items to Zabbix. This is the default '
                                       'behaviour even if option is not specified')
        zabbix_options.add_option('--discovery', action='store_const',
                                  dest='mode', const='discovery',
                                  help='If specified, will perform Zabbix Low Level '
                                       'Discovery on Hadoop Cloudera Manager API. '
                                       'Default is to get & send items')
        parser.add_option_group(zabbix_options)
        parser.set_defaults(mode='update_items')

        return parser

    def _setup_logging(self, zbx_container):
        logger = logging.getLogger(self.__class__.__name__)
        common_log_format = '[%(name)s:%(levelname)s] %(message)s'
        # Enable default console logging
        # Only if we have a tty (zabbix-agent redirects stdout)
        if sys.stdout.isatty():
            consoleHandler = logging.StreamHandler()
            consoleFormatter = logging.Formatter(
                fmt = common_log_format,
                datefmt = '%Y%m%d:%H%M%S'
            )
            consoleHandler.setFormatter(consoleFormatter)
            logger.addHandler(consoleHandler)
        # zabbix_agent uses syslog if LogFile empty, specified file otherwise
        if zbx_container.log_output:
            try:
                # TODO use Datacontainer.log_output property
                fileHandler = logging.FileHandler('/tmp/zabbix_agentd.log')
                # Use same date format as Zabbix: when logging into
                # zabbix_agentd log file, it's easier to read & parse
                logFormatter = logging.Formatter(
                    fmt = '%(process)d:%(asctime)s.%(msecs)03d ' + common_log_format,
                    datefmt = '%Y%m%d:%H%M%S'
                )
                fileHandler.setFormatter(logFormatter)
                logger.addHandler(fileHandler)
            except IOError:
                pass
        else:
            syslogHandler = logging.handlers.SysLogHandler(
                address = '/dev/log',
                facility = logging.handlers.SysLogHandler.LOG_DAEMON
            )
            # Use same date format as Zabbix does: when logging into
            # zabbix_agentd log file, it's easier to read & parse
            logFormatter = logging.Formatter(
                fmt = '%(process)d:%(asctime)s.%(msecs)03d ' + common_log_format,
                datefmt = '%Y%m%d:%H%M%S'
            )
            syslogHandler.setFormatter(logFormatter)
            logger.addHandler(syslogHandler)
        logger.setLevel(
            self.LOG_LEVEL[zbx_container.log_level]
        )
        return logger

    def _init_container(self):
        zbx_container = DataContainer(
            data_type = 'items',
            zbx_host  = self.options.zabbix_server,
            zbx_port  = int(self.options.zabbix_port),
            log_level = 4 if self.options.debug else 3,
            dryrun    = self.options.dry,
            logger    = self.logger
        )
        return zbx_container

    def run(self):
        (self.options, args) = self._parse_args()
        self.hostname = socket.getfqdn()

        # Datacontainer init (needs logger)
        zbx_container = self._init_container()
        # logger init
        self.logger = zbx_container.logger = self._setup_logging(zbx_container)

        # Step 1: read probe configuration
        try:
            self._init_probe()
        except Exception as e:
            self.logger.error('Step 1 - Read probe configuration failed')
            self.logger.debug(traceback.format_exc())
            return 1

        # Step 2: get data
        try:
            data = {}
            if self.options.mode == "update_items":
                zbx_container.data_type = 'items'
                data = self._get_metrics()
            elif self.options.mode == "discovery":
                zbx_container.data_type = 'lld'
                data = self._get_discovery()
        except Exception as e:
            self.logger.error(
                'Step 2 - Get Data failed [%s]' % str(e)
            )
            self.logger.debug(traceback.format_exc())
            return 2

        # Step 3: format & load data into container
        try:
            zbx_container.add(data)
        except Exception as e:
            self.logger.error(
                'Step 3 - Format & add Data failed [%s]' % e.strerror
            )
            self.logger.debug(traceback.format_exc())
            return 3

        # Step 4: send container data to Zabbix server
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
                'Step 4 - Unknown error [%s]' % e.strerror
            )
            self.logger.debug(traceback.format_exc())
            return 4
        # Everything went fine. Let's return 0 and exit
        return 0
