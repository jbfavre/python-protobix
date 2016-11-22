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
ZBX_DBG_SEND_RESULT = "Send result [%s-%s-%s] for key [%s] item [%s]. Server's response is %s"
ZBX_TRAPPER_MAX_VALUE = 250

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
                self.logger.error("Setup data_type before adding data")
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
        if self.logger: # pragma: no cover
            self.logger.info("Starting to send %d items" % len(self._items_list))
        try:
            # Zabbix trapper send a maximum of 250 items in bulk
            # We have to respect that, in case of enforcement on zabbix server side
            # Special case if debug is enabled: we need to send items one by one
            max_value = ZBX_TRAPPER_MAX_VALUE
            if self.debug_level >= 4:
                max_value = 1
                if self.logger: # pragma: no cover
                    self.logger.debug("Bulk limit is %d items" % max_value)
            else:
                if self.logger: # pragma: no cover
                    self.logger.info("Bulk limit is %d items" % max_value)
            # Initialize offsets & counters
            max_offset = len(self._items_list)
            run = 0
            start_offset = 0
            stop_offset = min(start_offset + max_value, max_offset)
            server_success = server_failure = processed = failed = total = time = 0
            while start_offset < stop_offset:
                run += 1
                if self.logger: # pragma: no cover
                    self.logger.debug(
                        'run %d: start_offset is %d, stop_offset is %d' %
                        (run, start_offset, stop_offset)
                    )

                # Extract items to be send from global item's list'
                _items_to_send = self.items_list[start_offset:stop_offset]

                # Send extracted items
                run_response, run_processed, run_failed, run_total, run_time = self._send_common(_items_to_send)

                # Update counters
                if run_response == 'success':
                    server_success += 1
                elif run_response == 'failed':
                    server_failure += 1
                processed += run_processed
                failed += run_failed
                total += run_total
                time += run_time
                if self.logger: # pragma: no cover
                    self.logger.info("%d items sent during run %d" % (run_total, run))
                    self.logger.debug(
                        'run %d: processed is %d, failed is %d, total is %d' %
                        (run, run_processed, run_failed, run_total)
                    )

                # Compute next run's offsets
                start_offset = stop_offset
                stop_offset = min(start_offset + max_value, max_offset)

                # Reset socket, which is likely to be closed by server
                self._socket_reset()
        except:
            self._reset()
            self._socket_reset()
            raise
        if self.logger: # pragma: no cover
            self.logger.info('All %d items have been sent in %d runs' % (total, run))
            self.logger.debug(
                'Total run is %d; item processed: %d, failed: %d, total: %d, during %f seconds' %
                (run, processed, failed, total, time)
            )
        # Everything has been sent.
        # Reset DataContainer & return results_list
        self._reset()
        return server_success, server_failure, processed, failed, total, time

    def _send_common(self, item):
        """
        Common part of sending operations
        Calls SenderProtocol._send_to_zabbix
        Returns result as provided by _handle_response

        :item: either a list or a single item depending on debug_level
        """
        total = len(item)
        processed = failed = time = 0
        if self._config.dryrun is True:
            total = len(item)
            processed = failed = time = 0
            response = 'dryrun'
        else:
            self._send_to_zabbix(item)
            response, processed, failed, total, time = self._read_from_zabbix()

        output_key = '(bulk)'
        output_item = '(bulk)'
        if self.debug_level >= 4:
            output_key = item[0]['key']
            output_item = item[0]['value']
        if self.logger: # pragma: no cover
            self.logger.info(
                "" +
                ZBX_DBG_SEND_RESULT % (
                    processed,
                    failed,
                    total,
                    output_key,
                    output_item,
                    response
                )
            )
        return response, processed, failed, total, time

    def _reset(self):
        """
        Reset main DataContainer properties
        """
        # Reset DataContainer to default values
        # So that it can be reused
        if self.logger: # pragma: no cover
            self.logger.info("Reset DataContainer")
        self._items_list = []
        self._config.data_type = None

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
                self._logger.error("logger requires a logging instance")
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
