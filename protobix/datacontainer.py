import time
import configobj
import logging
import warnings, functools
try: import simplejson as json
except ImportError: import json
from datetime import datetime

import sys
if sys.version_info < (3,):
    def deprecated(func):
        '''This is a decorator which can be used to mark functions
        as deprecated. It will result in a warning being emitted
        when the function is used.'''

        @functools.wraps(func)
        def new_func(*args, **kwargs):
            warnings.warn_explicit(
                "Call to deprecated function {}.".format(func.__name__),
                category=DeprecationWarning,
                filename=func.func_code.co_filename,
                lineno=func.func_code.co_firstlineno + 1
            )
            return func(*args, **kwargs)
        return new_func
else:
    def deprecated(func):
        '''This is a decorator which can be used to mark functions
        as deprecated. It will result in a warning being emitted
        when the function is used.'''

        @functools.wraps(func)
        def new_func(*args, **kwargs):
            warnings.warn_explicit(
                "Call to deprecated function {}.".format(func.__name__),
                category=DeprecationWarning,
                filename=func.__code__.co_filename,
                lineno=func.__code__.co_firstlineno + 1
            )
            return func(*args, **kwargs)
        return new_func

from .senderprotocol import SenderProtocol

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
                       dryrun     = False,
                       logger     = None):
        super(DataContainer,self).__init__()


        # Loads config from zabbix_agentd file
        # If no file, it uses the default _config as configuration
        self._load_zabbix_config(zbx_file)
        # Override default values with the ones provided
        if log_level:
            self._config['log_level'] = log_level
        if log_output != None:
            self._config['log_output'] = log_output
        self._config['dryrun'] = dryrun
        if zbx_host:
            self._config['server'] = zbx_host
        if zbx_port:
            self._config['port'] = zbx_port
        if data_type:
            self._config['data_type'] = data_type
        self._logger = logger

    @property
    def data_type(self):
        return self._config['data_type']

    @data_type.setter
    def data_type(self, value):
        if self._logger:
            self._logger.debug("Setting value %s as data_type" % value)
        if value in ['lld', 'items']:
          self._config['data_type'] = value
          # Clean _items_list & _result when changing _data_type
          # Incompatible format
          self._items_list = []
          self._result = []
        else:
            if self._logger:
                self._logger.error('data_type requires either "items" or "lld"')
            raise ValueError('data_type requires either "items" or "lld"')

    @property
    def log_level(self):
        return int(self._config['log_level'])

    @log_level.setter
    def log_level(self, value):
        if isinstance(value, int) and value >= 0 and value < 5:
            self._config['log_level'] = value
        else:
            if self._logger:
                self._logger.error('log_level parameter must be less than 5')
            raise ValueError('log_level parameter must be less than 5')

    @property
    def dryrun(self):
        return self._config['dryrun']

    @dryrun.setter
    def dryrun(self, value):
        if value in [True, False]:
            self._config['dryrun'] = value
        else:
            if self._logger:
                self._logger.error('dryrun parameter requires boolean')
            raise ValueError('dryrun parameter requires boolean')

    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, value):
        if isinstance(value, logging.Logger):
            self._logger = value
        else:
            if self._logger:
                self._logger.error('logger requires a logging instance')
            raise ValueError('logger requires a logging instance')

    @property
    def log_output(self):
        return self._config['log_output']

    def _load_zabbix_config(self,config_file):
        # Load zabbix agent configuration as default values
        # Default values are set in self._config
        # - ServerActive (default: 127.0.0.1)
        # - LogFile (default: /tmp/zabbix_agentd.log)
        # - DebugLevel (default: 3, Allowed: 0-4)
        #               0 -> logging.NOTSET
        #               1 -> logging.CRITICAL
        #               2 -> logging.ERROR
        #               3 -> logging.WARNING
        #               4 -> logging.DEBUG
        # - Timeout (default: 3, Allowed: 1-30)
        tmp_config = configobj.ConfigObj(config_file, list_values=False)

        if 'ServerActive' in tmp_config:
            tmp_server = tmp_config['ServerActive'][0] \
                         if isinstance(tmp_config['ServerActive'], list) \
                         else list(tmp_config['ServerActive'])[0]
            self._config['server'], self._config['port'] = tmp_server.split(':') \
                         if ":" in tmp_server else (tmp_server, 10051)

        if 'LogFile' in tmp_config:
            self._config['log_output'] = tmp_config['LogFile']

        if 'DebugLevel' in tmp_config:
            self._config['log_level'] = int(tmp_config['DebugLevel'])

        if 'Timeout' in tmp_config:
            self._config['timeout'] = int(tmp_config['Timeout'])

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
            if self._logger:
                self._logger.error('Setup data_type before adding data')
            raise ValueError('Setup data_type before adding data')
        self._items_list.append(item)

    def add(self, data):
        for host in data:
            for key in data[host]:
                if not data[host][key] == []:
                    self.add_item( host, key, data[host][key])

    @deprecated
    def set_type(self, value):
        self.data_type = value
