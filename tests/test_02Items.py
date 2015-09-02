import pytest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import protobix
import logging

class TestItems(object):

    data = {
        "myhost1": {
            "my.zabbix.item1": 0,
            "my.zabbix.item2": "item string"
        },
        "myhost2": {
            "my.zabbix.item1": 0,
            "my.zabbix.item2": "item string"
        }
    }
    data_type = 'items'

    @classmethod
    def setup_class(cls):
        common_log_format = '[%(name)s:%(levelname)s] %(message)s'
        cls.logger = logging.getLogger(cls.__class__.__name__)
        consoleHandler = logging.StreamHandler()
        consoleFormatter = logging.Formatter(
            fmt = common_log_format,
            datefmt = '%Y%m%d:%H%M%S'
        )
        consoleHandler.setFormatter(consoleFormatter)
        cls.logger.addHandler(consoleHandler)

        cls.zbx_container = protobix.DataContainer(logger=cls.logger)
        cls.zbx_container._items_list = []
        cls.zbx_container._config = {
            'server': '127.0.0.1',
            'port': 10051,
            'log_level': 3,
            'log_output': '/tmp/zabbix_agentd.log',
            'dryrun': False,
            'data_type': None,
            'timeout': 3,
        }

    @classmethod
    def teardown_class(cls):
        cls.zbx_container._items_list = []
        cls.zbx_container._config = {
            'server': '127.0.0.1',
            'port': 10051,
            'log_level': 3,
            'log_output': '/tmp/zabbix_agentd.log',
            'dryrun': False,
            'data_type': None,
            'timeout': 3,
        }
        cls.zbx_container = None
        cls.logger = None

    def setup_method(self, method):
        self.zbx_container._items_list = []
        self.zbx_container._config = {
            'server': '127.0.0.1',
            'port': 10051,
            'log_level': 3,
            'log_output': '/tmp/zabbix_agentd.log',
            'dryrun': False,
            'data_type': None,
            'timeout': 3,
        }

    def teardown_method(self, method):
        self.zbx_container._items_list = []
        self.zbx_container._config = {
            'server': '127.0.0.1',
            'port': 10051,
            'log_level': 3,
            'log_output': '/tmp/zabbix_agentd.log',
            'dryrun': False,
            'data_type': None,
            'timeout': 3,
        }

    def testAddBeforeSettingData_type(self):
        assert self.zbx_container.items_list == []
        with pytest.raises(ValueError):
            self.zbx_container.add(self.data)
        assert self.zbx_container.items_list == []

    def testNoDebugNoDryrunSent(self):
        self.zbx_container.data_type = self.data_type
        assert self.zbx_container.items_list == []
        self.zbx_container.add(self.data)
        assert len(self.zbx_container.items_list) == 4
        ''' Send data to zabbix '''
        self.zbx_container.send()
        assert len(self.zbx_container.result) == 1
        for result in self.zbx_container.result:
            assert result[0] == '4'
            assert result[1] == '0'
            assert result[2] == '4'
        assert self.zbx_container.items_list == []

    def testDebugNoDryrunSent(self):
        self.zbx_container.data_type = self.data_type
        self.zbx_container.log_level = 4
        self.zbx_container.add(self.data)
        assert len(self.zbx_container.items_list) == 4
        ''' Send data to zabbix '''
        self.zbx_container.send()
        assert len(self.zbx_container.result) == 4
        for result in self.zbx_container.result: 
            assert result[0] == '1'
            assert result[1] == '0'
            assert result[2] == '1'
        assert self.zbx_container.items_list == []

    def testNoDebugDryrunSent(self):
        self.zbx_container.data_type = self.data_type
        self.zbx_container.dryrun = True
        assert self.zbx_container.items_list == []
        self.zbx_container.add(self.data)
        assert len(self.zbx_container.items_list) == 4
        ''' Send data to zabbix '''
        self.zbx_container.send()
        assert self.zbx_container.result == [['d', 'd', '4']]
        assert self.zbx_container.items_list == []

    def testDebugDryrunSent(self):
        self.zbx_container.data_type = self.data_type
        self.zbx_container.dryrun = True
        self.zbx_container.log_level = 4
        assert self.zbx_container.items_list == []
        self.zbx_container.add(self.data)
        assert len(self.zbx_container.items_list) == 4
        ''' Send data to zabbix '''
        assert self.zbx_container.result == []
        self.zbx_container.send()
        for result in self.zbx_container.result:
            assert result == ['d', 'd', '1']
        assert self.zbx_container.items_list == []

    def testServerConnectionFails(self):
        self.zbx_container.zbx_port = 10052
        self.zbx_container.data_type = self.data_type
        assert self.zbx_container.items_list == []
        self.zbx_container.add(self.data)
        ''' Send data to zabbix '''
        with pytest.raises(IOError):
            self.zbx_container.send()
        assert self.zbx_container.result == []
        assert self.zbx_container.items_list == []