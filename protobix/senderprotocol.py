import socket
import struct
import time
import sys
import warnings,functools
try: import simplejson as json
except ImportError: import json

from .zabbixagentconfig import ZabbixAgentConfig

if sys.version_info < (3,):
    def b(x):
        return x
else:
    import codecs
    def b(x):
        return codecs.utf_8_encode(x)[0]

ZBX_HDR = "ZBXD\1"
ZBX_HDR_SIZE = 13

class SenderProtocol(object):

    REQUEST = "sender data"

    def __init__(self):
        self._zbx_config = ZabbixAgentConfig()
        self._pbx_config = {
            'timeout': self._zbx_config.timeout
        }
        self._pbx_config['dryrun'] = False
        self._items_list = []
        self._data = None
        self._result = None

    @property
    def zbx_host(self):
        return self._zbx_config.server_active

    @zbx_host.setter
    def zbx_host(self, value):
        self._zbx_config.server_active = value

    @property
    def zbx_port(self):
        return self._zbx_config.server_port

    @zbx_port.setter
    def zbx_port(self, value):
        self._zbx_config.server_port = value

    @property
    def items_list(self):
        return self._items_list

    @property
    def result(self):
        return self._result

    @property
    def dryrun(self):
        return self._pbx_config['dryrun']

    @dryrun.setter
    def dryrun(self, value):
        if value in [True, False]:
            self._pbx_config['dryrun'] = value
        else:
            raise ValueError('dryrun parameter requires boolean')

    @property
    def log_level(self):
        return self._zbx_config.debug_level

    @log_level.setter
    def log_level(self, value):
        self._zbx_config.debug_level = value

    @property
    def clock(self):
        return int(time.time())

    def _send_to_zabbix(self, item):
        # Return 0 if dryrun mode enabled
        if self._pbx_config['dryrun']:
            return 0
        # Format data to be sent
        if type(item) is dict:
            item = [ item ]
        self._data = json.dumps({ "data": item,
                                 "request": self.REQUEST,
                                 "clock": self.clock })
        # Set socket options & open connection
        socket.setdefaulttimeout(self._zbx_config.timeout)
        try:
            self.zbx_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.zbx_sock.connect((self._zbx_config.server_active, self._zbx_config.server_port))
        except Exception as e:
            # Maybe we could consider storing missed sent data for later retry
            self._data = None
            self._items_list = []
            self.zbx_sock.close()
            raise
        # Build Zabbix Sender payload
        data_length = len(self._data)
        data_header = struct.pack('<Q', data_length)
        packet = b(ZBX_HDR) + data_header + b(self._data)
        # Send payload to Zabbix Server and check response header
        try:
            self.zbx_sock.sendall(packet)
        except:
            raise

        try:
            # Check the 5 first bytes from answer to ensure it's well formatted
            zbx_srv_resp_hdr = self.zbx_sock.recv(5)
            assert(zbx_srv_resp_hdr == b(ZBX_HDR))
        except Exception as e:
            raise
        # Get the 8 next bytes and unpack to get response's payload length
        zbx_srv_resp_data_hdr = self.zbx_sock.recv(8)
        zbx_srv_resp_body_len = struct.unpack('<Q', zbx_srv_resp_data_hdr)[0]
        # Get response payload from Zabbix Server
        zbx_srv_resp_body = self.zbx_sock.recv(zbx_srv_resp_body_len)
        self._data = None
        self._items_list = []
        self.zbx_sock.close()
        if sys.version_info[0] == 3:
            zbx_srv_resp_body = zbx_srv_resp_body.decode()
        return json.loads(zbx_srv_resp_body)
