import re
import socket
import struct
import time
import sys
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

ZBX_HDR = "ZBXD\1"
ZBX_HDR_SIZE = 13
# For both 2.0 & >2.2 Zabbix version
# ? 1.8: Processed 0 Failed 1 Total 1 Seconds spent 0.000057
# 2.0: Processed 0 Failed 1 Total 1 Seconds spent 0.000057
# 2.2: processed: 50; failed: 1000; total: 1050; seconds spent: 0.09957
# 2.4: processed: 50; failed: 1000; total: 1050; seconds spent: 0.09957
ZBX_RESP_REGEX = r'[Pp]rocessed:? (\d+);? [Ff]ailed:? (\d+);? [Tt]otal:? (\d+);? [Ss]econds spent:? (\d+\.\d+)'
ZBX_DBG_SEND_RESULT = "Send result [%s-%s-%s] for %s"
ZBX_DBG_SEND_ITEM   = "[%s %s %s]"
ZBX_SEND_ITEM   = "[%d items]"

class SenderProtocol(object):
    def __init__(self):
        self._config = {
            'server': '127.0.0.1',
            'port': 10051,
            'log_output': '/tmp/zabbix_agentd.log',
            'log_level': 3,
            'timeout': 3,
            'dryrun': False,
            'data_type': None }
        self._items_list = []
        self.data = None
    
    @property
    def zbx_host(self):
        return self._config['server']

    @zbx_host.setter
    def zbx_host(self, value):
        self._config['server'] = value

    @property
    def zbx_port(self):
        return self._config['port']

    @zbx_port.setter
    def zbx_port(self, value):
        if isinstance(value, int) and \
           value > 0 and value < 65535:
            self._config['port'] = value
        else:
            if self._logger:
                self._logger.error('zbx_port requires a valid TCP port number')
            raise ValueError('zbx_port requires a valid TCP port number')

    @property
    def items_list(self):
        return self._items_list

    @property
    def result(self):
        return self._result

    @property
    def clock(self):
        return time.time()

    def _send_to_zabbix(self, item):
        # Return 0 if dryrun mode enabled
        if self._config['dryrun']:
            return 0
        # Format data to be sent
        if type(item) is dict:
            item = [ item ]
        self.data = json.dumps({ "data": item,
                                 "request": self.REQUEST,
                                 "clock": self.clock })
        # Set socket options & open connection
        socket.setdefaulttimeout(self._config['timeout'])
        try:
            self.zbx_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.zbx_sock.connect((self._config['server'], int(self._config['port'])))
        except Exception as e:
            # Maybe we could consider storing missed sent data for later retry
            self.data = None
            self._items_list = []
            self.zbx_sock.close()
            if self._logger:
                self._logger.error(
                    "Unable to connect to server %s on port %d" % \
                    (self._config['server'], self._config['port'])
                )
            raise
        # Build Zabbix Sender payload
        data_length = len(self.data)
        data_header = struct.pack('<Q', data_length)
        packet = b(ZBX_HDR) + data_header + b(self.data)
        # Send payload to Zabbix Server and check response header
        try:
            self.zbx_sock.sendall(packet)
        except:
            if self._logger:
                self._logger.error('Error while sending data to Zabbix server')
            raise

        try:
            # Check the 5 first bytes from answer to ensure it's well formatted
            zbx_srv_resp_hdr = self.zbx_sock.recv(5)
            assert(zbx_srv_resp_hdr == b(ZBX_HDR))
        except Exception as e:
            if self._logger:
                self._logger.error(
                    'Error while receiving response from Zabbix server [%s]' % e
                )
            raise
        # Get the 8 next bytes and unpack to get response's payload length
        zbx_srv_resp_data_hdr = self.zbx_sock.recv(8)
        zbx_srv_resp_body_len = struct.unpack('<Q', zbx_srv_resp_data_hdr)[0]
        # Get response payload from Zabbix Server
        zbx_srv_resp_body = self.zbx_sock.recv(zbx_srv_resp_body_len)
        self.data = None
        self._items_list = []
        self.zbx_sock.close()
        if sys.version_info[0] == 3:
            zbx_srv_resp_body = zbx_srv_resp_body.decode()
        return json.loads(zbx_srv_resp_body)

    def send(self, container = None):
        if container != None and self.logger:
            # Using container argument is deprecated
            self.logger.warning(
                'Deprecated call of send() function with container argument'
            )
        zbx_answer = 0
        self._result = []
        if self._config['log_level'] >= 4:
            # Per item sent if debug mode enabled
            for item in self._items_list:
                output =  ZBX_DBG_SEND_ITEM % (
                    item["host"],
                    item["key"],
                    item["value"]
                )
                zbx_answer = self._send_to_zabbix(item)
                result = self._handle_response(zbx_answer, output)
                if self.logger:
                    self._logger.debug(
                        ZBX_DBG_SEND_RESULT % (
                            result[0],
                            result[1],
                            result[2],
                            output
                        )
                    )
                self._result.append(result)
        else:
            # All items at once if no debug
            output = ZBX_SEND_ITEM % (
                len(self._items_list)
            )
            zbx_answer = self._send_to_zabbix(self._items_list)
            result = self._handle_response(zbx_answer, output)
            if self.logger:
                self._logger.info(
                    ZBX_DBG_SEND_RESULT % (
                        result[0],
                        result[1],
                        result[2],
                        output
                    )
                )
            self._result.append(result)
        self.data = None
        self._items_list = []
        if not self._config['dryrun']:
            self.zbx_sock.close()
        self._config['data_type'] = None

    def _handle_response(self, zbx_answer, output):
        if zbx_answer and self.logger:
            self.logger.debug("Got [%s] as response from Zabbix server" % zbx_answer)
        nb_item = len(self._items_list)
        if self._config['log_level'] >= 4:
            nb_item = 1
        if zbx_answer:
            if zbx_answer.get('response') == 'success':
                result = re.findall( ZBX_RESP_REGEX, zbx_answer.get('info'))
                result = result[0]
        else:
            result = ['d', 'd', str(nb_item)]
        return result

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
        if self._config['log_level'] >= 4:
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
