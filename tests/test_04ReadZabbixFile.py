import pytest, coverage
import unittest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import protobix
import logging

class TestZabbixFile(object):

#   @classmethod
#   def setup_class(cls):
#       common_log_format = '[%(name)s:%(levelname)s] %(message)s'
#       cls.logger = logging.getLogger(cls.__class__.__name__)
#       consoleHandler = logging.StreamHandler()
#       consoleFormatter = logging.Formatter(
#           fmt = common_log_format,
#           datefmt = '%Y%m%d:%H%M%S'
#       )
#       consoleHandler.setFormatter(consoleFormatter)
#       cls.logger.addHandler(consoleHandler)

#       cls.zbx_container = protobix.DataContainer(logger=cls.logger)
#       cls.zbx_container._items_list = []
#       cls.zbx_container._config = {
#           'server': '127.0.0.1',
#           'port': 10051,
#           'log_level': 3,
#           'log_output': '/tmp/zabbix_agentd.log',
#           'dryrun': False,
#           'data_type': None,
#           'timeout': 3
#       }

#   @classmethod
#   def teardown_class(cls):
#       cls.zbx_container._items_list = []
#       cls.zbx_container._config = {
#           'server': '127.0.0.1',
#           'port': 10051,
#           'log_level': 3,
#           'log_output': '/tmp/zabbix_agentd.log',
#           'dryrun': False,
#           'data_type': None,
#           'timeout': 3
#       }
#       cls.zbx_container = None
#       cls.logger = None

#   def setup_method(self, method):
#       self.zbx_container._items_list = []
#       self.zbx_container._config = {
#           'server': '127.0.0.1',
#           'port': 10051,
#           'log_level': 3,
#           'log_output': '/tmp/zabbix_agentd.log',
#           'dryrun': False,
#           'data_type': None,
#           'timeout': 3
#       }

#   def teardown_method(self, method):
#       self.zbx_container._items_list = []
#       self.zbx_container._config = {
#           'server': '127.0.0.1',
#           'port': 10051,
#           'log_level': 3,
#           'log_output': '/tmp/zabbix_agentd.log',
#           'dryrun': False,
#           'data_type': None,
#           'timeout': 3
#       }

    def test_default_params(self):
        self.zbx_container = protobix.DataContainer(
                        data_type  = 'items',
        )
        assert self.zbx_container._config == {
            'server': '127.0.0.1',
            'port': 10051,
            'log_level': 3,
            'log_output': '/tmp/zabbix_agentd.log',
            'dryrun': False,
            'data_type': 'items',
            'timeout': 3
        }

    def test_custom_params(self):
        self.zbx_container = protobix.DataContainer(
                        data_type  = 'items',
                        zbx_file   = './tests/zabbix_agentd.conf',
        )
        assert self.zbx_container._config == {
            'server': '127.0.1.1',
            'port': 10061,
            'log_level': 3,
            'log_output': '/tmp/test_zabbix_agentd.log',
            'dryrun': False,
            'data_type': 'items',
            'timeout': 3
        }
