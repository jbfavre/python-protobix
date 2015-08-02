import time
import logging
import warnings, functools
try: import ujson as json
except ImportError: import json

from .senderprotocol import SenderProtocol

def deprecated(func):

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        print ((
            "Call to deprecated function %s" % (
                str(func.__name__)
            )
        ))
        return func(*args, **kwargs)
    return new_func

class DataContainer(SenderProtocol):

    REQUEST = "sender data"
    _data_type = None
    _items_list = []

    def __init__(self, data_type  = None,
                       zbx_file   = '/etc/zabbix/zabbix_agentd.conf',
                       zbx_host   = None,
                       zbx_port   = None,
                       log_level  = None,
                       log_output = None,
                       dryrun     = False):

        # try to load config from zabbix_agentd file
        # If no file, it loads the default _config as configuration
        self._load_config(zbx_file)
        # Override default values with the ones provided
        if log_level:
            self._config['log_level'] = log_level
        if log_output:
            self._config['log_output'] = log_output
        self._config['dryrun'] = dryrun
        if zbx_host:
            self._config['server'] = zbx_host
        if zbx_port:
            self._config['port'] = zbx_port
        if data_type:
            self._config['data_type'] = data_type

    @property
    def data_type(self):
        return self._config['data_type']

    @data_type.setter
    def data_type(self, value):
        if value in ['lld', 'items']:
          self._config['data_type'] = value
          # Clean _items_list & _result when changing _data_type
          # Incompatible format
          self._items_list = []
          self._result = []
        else:
            raise ValueError('Only support either "items" or "lld"')

    @property
    def clock(self):
        return int((time.time())/60*60)

    @deprecated
    def set_type(self, value):
        self.data_type = value

    def add_item(self, host, key, value, clock=None):
        if clock is None:
            clock = self.clock
        if self._config['data_type'] == "items":
            item = { "host": host, "key": key,
                     "value": value, "clock": clock}
        elif self._config['data_type'] == "lld":
            item = { "host": host, "key": key, "clock": clock,
                     "value": json.dumps({"data": value}) }
        else:
            raise ValueError('Setup data_type before adding data')
        self._items_list.append(item)

    def add(self, data):
        for host in data:
            for key in data[host]:
                if not data[host][key] == []:
                    self.add_item( host, key, data[host][key])