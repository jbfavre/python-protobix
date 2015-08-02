import re
import socket
import struct
import time
import sys
import configobj
import logging
import warnings,functools
try: import simplejson as json
except ImportError: import json

if sys.version_info < (3,):
    def b(x):
        return x
else:
    import codecs
    def b(x):
        return codecs.utf_8_encode(x)[0]

from .senderexception import SenderException

ZBX_HDR = "ZBXD\1"
ZBX_HDR_SIZE = 13
# For both 2.0 & >2.2 Zabbix version
# ? 1.8: Processed 0 Failed 1 Total 1 Seconds spent 0.000057
# 2.0: Processed 0 Failed 1 Total 1 Seconds spent 0.000057
# 2.2: processed: 50; failed: 1000; total: 1050; seconds spent: 0.09957
# 2.4: processed: 50; failed: 1000; total: 1050; seconds spent: 0.09957
ZBX_RESP_REGEX = r'[Pp]rocessed:? (\d+);? [Ff]ailed:? (\d+);? [Tt]otal:? (\d+);? [Ss]econds spent:? (\d+\.\d+)'
ZBX_DBG_SEND_RESULT = "Send result [%s-%s-%s] for [%s %s %s]"

class SenderProtocol(object):

    _config = {
        'server': '127.0.0.1',
        'port': 10051,
        'log_output': '/tmp/zabbix_agentd.log',
        'log_level': 3,
        'timeout': 3,
        'dryrun': False,
        'data_type': None
    }
    LOG_LVL = [
        logging.NOTSET,
        logging.CRITICAL,
        logging.ERROR,
        logging.WARNING,
        logging.DEBUG
    ]

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

    @property
    def zbx_host(self):
        return self._config['server']

    @zbx_host.setter
    def zbx_host(self, value):
        self._config['server'] = value

    @property
    def log_level(self):
        return int(self._config['log_level'])

    @log_level.setter
    def log_level(self, value):
        if isinstance(value, int) and value >= 0 and value < 5:
            self._config['log_level'] = value
        else:
            raise ValueError('log_level parameter must be less than 5')

    @property
    def zbx_port(self):
        return self._config['port']

    @zbx_port.setter
    def zbx_port(self, value):
        if isinstance(value, int) and \
           value > 0 and value < 65535:
            self._config['port'] = value
        else:
            raise ValueError('zbx_port requires a valid TCP port number')

    @property
    def dryrun(self):
        return self._config['dryrun']

    @dryrun.setter
    def dryrun(self, value):
        if value in [True, False]:
            self._config['dryrun'] = value
        else:
            raise ValueError('dryrun parameter requires boolean')

    @property
    def items_list(self):
        return self._items_list

    @property
    def result(self):
        return self._result

    def _load_config(self,config_file):
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
        tmp_config = configobj.ConfigObj(config_file)

        if 'ServerActive' in tmp_config:
            tmp_server = tmp_config['ServerActive'][0] \
                         if isinstance(tmp_config['ServerActive'], list) \
                         else tmp_config['ServerActive']
            self._config['server'], self._config['port'] = tmp_server.split(':') \
                         if ":" in tmp_server else (tmp_server, 10051)

        if 'LogFile' in tmp_config:
            self._config['log_output'] = tmp_config['LogFile']

        if 'DebugLevel' in tmp_config:
            self._config['log_level'] = int(tmp_config['DebugLevel'])

        if 'Timeout' in tmp_config:
            self._config['timeout'] = int(tmp_config['Timeout'])

    def _send_to_zabbix(self, item):
        # Format data to be sent
        if type(item) is dict:
            item = [ item ]
        data = json.dumps({ "data": item,
                            "request": self.REQUEST,
                            "clock": self.clock })
        # Set socket options & open connection
        socket.setdefaulttimeout(1)
        try:
            zbx_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            zbx_sock.connect((self._config['server'], int(self._config['port'])))
        except:
            # Maybe we could consider storing missed sent data for later retry
            self._items_list = []
            zbx_sock.close()
            raise SenderException(
                "Unable to connect to server %s on port %d" % \
                (self._config['server'], self._config['port'])
            )

        # Build Zabbix Sender payload
        data_length = len(data)
        data_header = struct.pack('<Q', data_length)
        packet = b(ZBX_HDR) + data_header + b(data)
        # Send payload to Zabbix Server and check response header
        try:
            zbx_sock.sendall(packet)
            # Check the 5 first bytes from answer to ensure it's well formatted
            zbx_srv_resp_hdr = zbx_sock.recv(5)
            assert(zbx_srv_resp_hdr == b(ZBX_HDR))
        except:
            raise SenderException('Invalid response from Zabbix server')

        # Get the 8 next bytes and unpack to get response's payload length
        zbx_srv_resp_data_hdr = zbx_sock.recv(8)
        zbx_srv_resp_body_len = struct.unpack('<Q', zbx_srv_resp_data_hdr)[0]
        # Get response payload from Zabbix Server
        zbx_srv_resp_body = zbx_sock.recv(zbx_srv_resp_body_len)
        zbx_sock.close()
        return json.loads(zbx_srv_resp_body)

    # Using container argument is deprecated
    def send(self, container = None):
        zbx_answer = 0
        self._result = []
        if self._config['log_level'] == 4:
            for item in self._items_list:
                if not self._config['dryrun']:
                    zbx_answer = self._send_to_zabbix(item)
                self._handle_response(zbx_answer, item)
        else:
            if not self._config['dryrun']:
                zbx_answer = self._send_to_zabbix(self._items_list)
            self._handle_response(zbx_answer)
        self._items_list = []
        self._config['data_type'] = None

    def _handle_response(self, zbx_answer, item=None):
        nb_item = len(self._items_list)
        if self._config['log_level'] == 4:
            nb_item = 1
        result = ['0', '0', '0']
        if not self._config['dryrun']:
            if zbx_answer.get('response') == 'success':
                result = re.findall( ZBX_RESP_REGEX, zbx_answer.get('info'))
                result = result[0]
        else:
            result = ['-', '-', str(nb_item)]
        if self._config['log_level'] == 4:
            print(( ZBX_DBG_SEND_RESULT % (result[0],
                                           result[1],
                                           result[2],
                                           item["host"],
                                           item["key"],
                                           item["value"])))
        self._result.append(result)

    @deprecated
    def set_debug(self, value):
        if value:
            self._config['log_level'] = 4
        else:
            self._config['log_level'] = 3

    @deprecated
    def set_verbosity(self, value):
        pass

    @deprecated
    def set_dryrun(self, value):
        if value == None:
            value = False
        self._config['dryrun'] = value

    @deprecated
    def set_host(self, value):
        self._config['server'] = value

    @deprecated
    def set_port(self, value):
        self._config['port'] = value

    @property
    @deprecated
    def debug(self):
        if self._config['log_level'] == 4:
            return True
        else:
            return False

    @debug.setter
    @deprecated
    def debug(self, value):
        if value in [True, False]:
            if value is True:
                self._config['log_level'] = 4
            else:
                self._config['log_level'] = 3
        else:
            raise ValueError('debug parameter requires boolean')