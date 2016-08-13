import re
import logging
try: import simplejson as json
except ImportError: import json # pragma: no cover

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
    _logger = None
    _config = None
    socket = None

    def __init__(self,
                 config=None,
                 logger=None):

        # Loads config from zabbix_agentd file
        # If no file, it uses the default _config as configuration
        self._config = config
        if config is None:
            self._config = ZabbixAgentConfig()
        if logger:
            self.logger = logger
        self._items_list = []

    def add_item(self, host, key, value, clock=None):
        """
        Add a single item into DataContainer

        :host: hostname to which item will be linked to
        :key: item key as defined in Zabbix
        :value: item value
        :clock: timestemp as integer. If not provided self.clock()) will be used
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
            if self.logger: # pragma: no cover
                self.logger.error("["+__class__.__name__+"] Setup data_type before adding data")
            raise ValueError('Setup data_type before adding data')
        self._items_list.append(item)

    def add(self, data):
        """
        Add a list of item into the container

        :data: dict of items & value per hostname
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

        :item: either a list or a single item depending on debug_level
        """
        zbx_answer = 0
        if self._config.dryrun is False:
            self._send_to_zabbix(item)
            zbx_answer = self._read_from_zabbix()
        result = self._handle_response(zbx_answer)
        if self.logger: # pragma: no cover
            output_key = '(bulk)'
            output_item = '(bulk)'
            if self.debug_level >= 4:
                output_key = item['key']
                output_item = item['value']
            self.logger.info(
                "["+__class__.__name__+"] " +
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
        """
        # Reset DataContainer to default values
        # So that it can be reused
        if self.logger: # pragma: no cover
            self.logger.info("["+__class__.__name__+"] Reset DataContainer")
        self._items_list = []
        self._config.data_type = None

    def _handle_response(self, zbx_answer):
        """
        Analyze Zabbix Server response
        Returns a list with number of:
        * processed items
        * failed items
        * total items
        * time spent

        :zbx_answer: Zabbix server response as JSON object
        """
        if self.logger: # pragma: no cover
            self.logger.info(
                "["+__class__.__name__+"] Anaylizing Zabbix Server's answer"
            )
            if zbx_answer:
                self.logger.debug("["+__class__.__name__+"] Zabbix Server response is: [%s]" % zbx_answer)
        # Default items number in length of th storage list
        nb_item = len(self._items_list)
        if self._config.debug_level >= 4:
            # If debug enabled, force it to 1
            nb_item = 1
        if zbx_answer and self._config.dryrun is False:
            # If dryrun is disabled, we can process answer
            if zbx_answer.get('response') == 'success':
                result = re.findall(ZBX_RESP_REGEX, zbx_answer.get('info'))
                result = result[0]
        else:
            # If dryrun is enabled, just force result
            result = ['d', 'd', str(nb_item), 'd']
        return result

    @property
    def logger(self):
        """
        Returns logger instance
        """
        return self._logger

    @logger.setter
    def logger(self, value):
        """
        Set logger instance for the class
        """
        if isinstance(value, logging.Logger):
            self._logger = value
        else:
            if self._logger: # pragma: no cover
                self._logger.error("["+__class__.__name__+"] logger requires a logging instance")
            raise ValueError('logger requires a logging instance')

    # ZabbixAgentConfig getter & setter
    # Avoid using private property _config from outside
    @property
    def dryrun(self):
        """
        Returns dryrun
        """
        return self._config.dryrun

    @dryrun.setter
    def dryrun(self, value):
        """
        Set dryrun
        """
        self._config.dryrun = value

    @dryrun.setter
    def data_type(self, value):
        """
        Set data_type
        """
        self._config.data_type = value
