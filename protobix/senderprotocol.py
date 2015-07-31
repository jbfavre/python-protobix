import re
import socket
import struct
import time
import sys
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

    @property
    def zbx_host(self):
        return self._zbx_host

    @zbx_host.setter
    def zbx_host(self, value):
        self._zbx_host = value

    # deprecated function
    def set_host(self, value):
        self._zbx_host = value

    @property
    def zbx_port(self):
        return self._zbx_port

    @zbx_port.setter
    def zbx_port(self, value):
        self._zbx_port = value

    # deprecated function
    def set_port(self, value):
        self.zbx_port = value

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        if value in [True, False]:
            self._debug = value
        else:
            raise ValueError('debug parameter requires boolean')

    # deprecated function
    def set_debug(self, value):
        self.debug = value

    # deprecated function
    def set_verbosity(self, value):
        return

    @property
    def dryrun(self):
        return self._dryrun

    @dryrun.setter
    def dryrun(self, value):
        if value in [True, False]:
            self._dryrun = value
        else:
            raise ValueError('dryrun parameter requires boolean')

    # deprecated function
    def set_dryrun(self, value):
        self.dryrun = value

    @property
    def items_list(self):
        return self._items_list

    @property
    def result(self):
        return self._result

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
            zbx_sock.connect((self.zbx_host, int(self.zbx_port)))
        except:
            # Maybe we could consider storing missed sent data for later retry
            self._items_list = []
            zbx_sock.close()
            raise SenderException('Unable to connect to Zabbix Server')

        # Build Zabbix Sender payload
        data_length = len(data)
        data_header = struct.pack('<Q', data_length)
        packet = b(ZBX_HDR) + data_header + b(data)
        # Send payload to Zabbix Server and check response header
        try:
            zbx_sock.send(packet)
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
        if self._debug:
            for item in self._items_list:
                if not self._dryrun:
                    zbx_answer = self._send_to_zabbix(item)
                self._handle_response(zbx_answer, item)
        else:
            if not self._dryrun:
                zbx_answer = self._send_to_zabbix(self._items_list)
            self._handle_response(zbx_answer)
        self._items_list = []

    def _handle_response(self, zbx_answer, item=None):
        nb_item = len(self._items_list)
        if self._debug:
            nb_item = 1
        if not self._dryrun:
            result = re.findall( ZBX_RESP_REGEX, zbx_answer.get('info'))
            result = result[0]
            self._result.append(result)
        else:
            result = ['0', '0', str(nb_item)]
            self._result.append(result)
            if self._debug:
                print((
                    ZBX_DBG_SEND_RESULT % (result[0],
                                           result[1],
                                           result[2],
                                           item["host"],
                                           item["key"],
                                           item["value"])))