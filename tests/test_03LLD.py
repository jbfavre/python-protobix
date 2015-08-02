import pytest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import protobix

class TestLLD:

    data = {
        'myhost1': {
            'my.zabbix.lld_item1': [
                { '{#ZBX_LLD_KEY11}': 0,
                  '{#ZBX_LLD_KEY12}': 'lld string' },
                { '{#ZBX_LLD_KEY11}': 1,
                  '{#ZBX_LLD_KEY12}': 'another lld string' }
            ]
        },
        'myhost2': {
            'my.zabbix.lld_item2': [
                { '{#ZBX_LLD_KEY21}': 10,
                  '{#ZBX_LLD_KEY21}': 'yet an lld string' },
                { '{#ZBX_LLD_KEY21}': 2,
                  '{#ZBX_LLD_KEY21}': 'yet another lld string' }
            ]
        }
    }
    data_type = 'lld'

    @classmethod
    def setup_class(cls):
        cls.zbx_container = protobix.DataContainer()
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
        ''' Send data to zabbix '''
        ret = self.zbx_container.send()
        assert self.zbx_container.items_list == []
        assert len(self.zbx_container.result) == 1
        for result in self.zbx_container.result:
            assert result[0] == '2'
            assert result[1] == '0'
            assert result[2] == '2'
        assert self.zbx_container.items_list == []

    def testDebugNoDryrunSent(self):
        self.zbx_container.log_level = 4
        self.zbx_container.data_type = self.data_type
        assert self.zbx_container.items_list == []
        self.zbx_container.add(self.data)
        assert len(self.zbx_container.items_list) == 2
        ''' Send data to zabbix '''
        ret = self.zbx_container.send()
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
        assert len(self.zbx_container.items_list) == 2
        ''' Send data to zabbix '''
        self.zbx_container.send()
        assert self.zbx_container.result == [['-', '-', '2']]
        assert self.zbx_container.items_list == []

    def testDebugDryrunSent(self):
        self.zbx_container.data_type = self.data_type
        self.zbx_container.dryrun = True
        self.zbx_container.log_level = 4
        assert self.zbx_container.items_list == []
        self.zbx_container.add(self.data)
        assert len(self.zbx_container.items_list) == 2
        ''' Send data to zabbix '''
        assert self.zbx_container.result == []
        self.zbx_container.send()
        for result in self.zbx_container.result:
            assert result == ['-', '-', '1']
        assert self.zbx_container.items_list == []

    def testZabbixConnectionFails(self):
        self.zbx_container.zbx_port = 10052
        self.zbx_container.data_type = self.data_type
        assert self.zbx_container.items_list == []
        self.zbx_container.add(self.data)
        ''' Send data to zabbix '''
        with pytest.raises(protobix.SenderException):
            ret = self.zbx_container.send()
        assert self.zbx_container.items_list == []