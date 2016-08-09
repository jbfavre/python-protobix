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

    _items_list = []
    _result = []

    def __init__(self, data_type=None,
                 zbx_file=None,
                 zbx_host=None,
                 zbx_port=None,
                 debug_level=None,
                 log_output=None,
                 dryrun=False,
                 logger=None):

        # Loads config from zabbix_agentd file
        # If no file, it uses the default _config as configuration
        self._config = ZabbixAgentConfig(zbx_file)
        # Override default values with the ones provided
        if debug_level:
            self.debug_level = debug_level
        if log_output is not None:
            self._config.log_file = log_output
        if zbx_host:
            self._config.server_active = zbx_host
        if zbx_port:
            self._config.server_port = zbx_port
        if data_type:
            self.data_type = data_type
        self._config.dryrun = dryrun
        self._logger = logger
        self._items_list = []
        self.socket = None

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

    def add_item(self, host, key, value, clock=None):
        """
        Add a snigle items into DataContainer
        Choose relevant format depending on data_type
        Provides clock information if not present
        Return nothing
        """
        if clock is None:
            clock = self.clock
        if self._config.data_type == "items":
            item = {"host": host, "key": key,
                    "value": value, "clock": clock}
        elif self._config.data_type == "lld":
            item = {"host": host, "key": key, "clock": clock,
                    "value": json.dumps({"data": value})}
        else:
            if self.logger:
                self.logger.error('Setup data_type before adding data')
            raise ValueError('Setup data_type before adding data')
        self._items_list.append(item)

    def add(self, data):
        """
        Add a list of item into the container
        Returns nothing
        """
        for host in data:
            for key in data[host]:
                if not data[host][key] == []:
                    self.add_item(host, key, data[host][key])

    def send(self):
        """
        Entrypoint to send data to Zabbix
        If debug is enabled, items are sent one by one
        If debug isn't enable, we send items in bulk
        Returns a list of results (1 if no debug, as many as items in other case)
        """
        results_list = []
        try:
            if self.debug_level >= 4:
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
        """
        Common part of sending operations
        Calls SenderProtocol._send_to_zabbix
        Returns result as provided by _handle_response
        """
        zbx_answer = 0
        if self._config.dryrun is False:
            self._send_to_zabbix(item)
            zbx_answer = self._read_from_zabbix()
        result = self._handle_response(zbx_answer)
        if self.logger:
            output_key = '(bulk)'
            output_item = '(bulk)'
            if self.debug_level >= 4:
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
        """
        Reset main DataContainer properties
        Avoid mixing items with LLD
        """
        # Reset DataContainer to default values
        # So that it can be reused
        self._items_list = []
        self._config.data_type = None

    def _handle_response(self, zbx_answer):
        """
        Analyze Zabbix Server response and extract informations from JSON body
        Returns a list with number of:
        * processed items
        * failed items
        * total items
        * time spent
        """
        if zbx_answer and self.logger:
            self.logger.debug("Zabbix Server response is: [%s]" % zbx_answer)
        nb_item = len(self._items_list)
        if self._config.debug_level >= 4:
            nb_item = 1
        if zbx_answer and self._config.dryrun is False:
            if zbx_answer.get('response') == 'success':
                result = re.findall(ZBX_RESP_REGEX, zbx_answer.get('info'))
                result = result[0]
        else:
            result = ['d', 'd', str(nb_item)]
        if self.logger and self._config.debug_level >= 5:
            self.logger.debug("Zabbix server results are: Processed: " + result[0])
            self.logger.debug("                              Failed: " + result[1])
            self.logger.debug("                               Total: " + result[2])
            if not self._config.dryrun:
                self.logger.debug("                                Time: " + result[3])
        return result

    # ZabbixAgentConfig getter & setter
    # Avoid using private property _config from outside
    @property
    def hostname(self):
        """
        Returns Hostname from ZabbixConfigAgent
        """
        return self._config.hostname

    @property
    def log_file(self):
        """
        Returns LogFile from ZabbixConfigAgent
        """
        return self._config.log_file

    @property
    def log_type(self):
        """
        Returns LogTyp from ZabbixConfigAgent
        """
        return self._config.log_type

    @property
    def dryrun(self):
        """
        Returns dryrun from ZabbixConfigAgent
        """
        return self._config.dryrun

    @dryrun.setter
    def dryrun(self, value):
        """
        Set dryrun to ZabbixConfigAgent
        """
        self._config.dryrun = value

    @property
    def data_type(self):
        """
        Returns data_type from ZabbixConfigAgent
        """
        return self._config.dryrun

    @dryrun.setter
    def data_type(self, value):
        """
        Set data_type to ZabbixConfigAgent
        """
        self._config.data_type = value
