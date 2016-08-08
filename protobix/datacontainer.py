import re
import logging
try: import simplejson as json
except ImportError: import json

from .zabbixagentconfig import ZabbixAgentConfig
from .senderprotocol import SenderProtocol

# For both 2.0 & >2.2 Zabbix version
# ? 1.8: Processed 0 Failed 1 Total 1 Seconds spent 0.000057
# 2.0: Processed 0 Failed 1 Total 1 Seconds spent 0.000057
# 2.2: processed: 50; failed: 1000; total: 1050; seconds spent: 0.09957
# 2.4: processed: 50; failed: 1000; total: 1050; seconds spent: 0.09957
ZBX_RESP_REGEX = r'[Pp]rocessed:? (\d+);? [Ff]ailed:? (\d+);? ' + \
                 r'[Tt]otal:? (\d+);? [Ss]econds spent:? (\d+\.\d+)'
ZBX_DBG_SEND_RESULT = "Send result [%s-%s-%s] for key [%s] item [%s]"

class DataContainer(SenderProtocol):

    _data_type = None
    _items_list = []
    _result = []

    def __init__(self, data_type=None,
                 zbx_file='/etc/zabbix/zabbix_agentd.conf',
                 zbx_host=None,
                 zbx_port=None,
                 log_level=None,
                 log_output=None,
                 dryrun=False,
                 logger=None):

        super(DataContainer, self).__init__()

        # Loads config from zabbix_agentd file
        # If no file, it uses the default _config as configuration
        self._zbx_config = ZabbixAgentConfig(zbx_file)
        self._pbx_config = {
            'dryrun': False,
            'data_type': None
        }
        # Override default values with the ones provided
        if log_level:
            self.log_level = log_level
        if log_output != None:
            self._zbx_config.log_file = log_output
        if zbx_host:
            self._zbx_config.server_active = zbx_host
        if zbx_port:
            self._zbx_config.server_port = zbx_port
        if data_type:
            self._pbx_config['data_type'] = data_type
        self._pbx_config['dryrun'] = dryrun
        self._logger = logger

    @property
    def data_type(self):
        return self._pbx_config['data_type']

    @data_type.setter
    def data_type(self, value):
        if self.logger:
            self.logger.debug("Setting value %s as data_type" % value)
        if value in ['lld', 'items']:
            if self.logger and self._pbx_config['data_type'] in ['lld', 'items']:
                self._logger.warning(
                    'data_type has been changed. Emptying DataContainer items list'
                )
            self._pbx_config['data_type'] = value
            # Clean _items_list & _result when changing _data_type
            # Incompatible format
            self._items_list = []
            self._result = []
        else:
            if self.logger:
                self._logger.error('data_type requires either "items" or "lld"')
            raise ValueError('data_type requires either "items" or "lld"')

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
    def hostname(self):
        return self._zbx_config.hostname

    @property
    def log_file(self):
        return self._zbx_config.log_file

    @property
    def log_type(self):
        return self._zbx_config.log_type

    def add_item(self, host, key, value, clock=None):
        if clock is None:
            clock = self.clock
        if self._pbx_config['data_type'] == "items":
            item = {"host": host, "key": key,
                    "value": value, "clock": clock}
        elif self._pbx_config['data_type'] == "lld":
            item = {"host": host, "key": key, "clock": clock,
                    "value": json.dumps({"data": value})}
        else:
            if self.logger:
                self.logger.error('Setup data_type before adding data')
            raise ValueError('Setup data_type before adding data')
        self._items_list.append(item)

    def add(self, data):
        for host in data:
            for key in data[host]:
                if not data[host][key] == []:
                    self.add_item(host, key, data[host][key])

    def send(self):
        results_list = []
        try:
            if self.log_level >= 4:
                # If debug mode enabled Sent one item at a time
                for item in self._items_list:
                    result = self._send_common(item)
                    results_list.append(result)
                    # With debug we need to reset socket after each sent
                    # But never reset DataContainer before all items sent
                    self._socket_reset()
            else:
                # If debug mode disabled Sent all items at once
                result = self._send_common(self._items_list)
                results_list.append(result)
        except:
            self._reset()
            self._socket_reset()
            raise
        self._reset()
        self._socket_reset()
        return results_list

    def _send_common(self, item):
        zbx_answer = 0
        if self.dryrun is False:
            self._send_to_zabbix(item)
            zbx_answer = self._read_from_zabbix()
        result = self._handle_response(zbx_answer)
        if self.logger:
            output_key = '(bulk)'
            output_item = '(bulk)'
            if self.log_level >= 4:
                output_key = item['key']
                output_item = item['value']
            self.logger.info(
                ZBX_DBG_SEND_RESULT % (
                    result[0],
                    result[1],
                    result[2],
                    output_key,
                    output_item
                )
            )
        return result

    def _reset(self):
        # Reset DataContainer to default values
        # So that it can be reused
        self._items_list = []
        self._pbx_config['data_type'] = None

    def _handle_response(self, zbx_answer):
        if zbx_answer and self.logger:
            self.logger.debug("Zabbix Server response is: [%s]" % zbx_answer)
        nb_item = len(self._items_list)
        if self._zbx_config.debug_level >= 4:
            nb_item = 1
        if zbx_answer and self.dryrun is False:
            if zbx_answer.get('response') == 'success':
                result = re.findall(ZBX_RESP_REGEX, zbx_answer.get('info'))
                result = result[0]
        else:
            result = ['d', 'd', str(nb_item)]
        if self.logger and self._zbx_config.debug_level >= 5:
            self.logger.debug("Zabbix server results are: Processed: " + result[0])
            self.logger.debug("                              Failed: " + result[1])
            self.logger.debug("                               Total: " + result[2])
            if not self.dryrun:
                self.logger.debug("                                Time: " + result[3])
        return result
