import socket
import struct
import time
import sys
import ssl
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
        self.socket = None

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
        if self.dryrun:
            return 0

        # Format data to be sent
        if type(item) is dict:
            item = [ item ]
        payload = json.dumps({ "data": item,
                                 "request": self.REQUEST,
                                 "clock": self.clock })
        data_length = len(payload)
        data_header = struct.pack('<Q', data_length)
        packet = b(ZBX_HDR) + data_header + b(payload)

        # Send payload to Zabbix Server
        self._socket().sendall(packet)

    def _read_from_zabbix(self):
        recv_length = 4096
        zbx_srv_resp_data = b''

        # Read Zabbix server answer
        while recv_length >= 4096:
            _buffer = self._socket().recv(4096)
            zbx_srv_resp_data += _buffer
            recv_length = len(_buffer)

        _buffer = None
        recv_length = None
        # Check that we have a valid Zabbix header mark
        assert(zbx_srv_resp_data[:5] == b(ZBX_HDR))

        # Extract response body length from packet
        zbx_srv_resp_body_len = struct.unpack('<Q', zbx_srv_resp_data[5:ZBX_HDR_SIZE])[0]

        # Extract response body
        zbx_srv_resp_body = zbx_srv_resp_data[ZBX_HDR_SIZE:ZBX_HDR_SIZE+zbx_srv_resp_body_len]

        # Check that we have read the whole packet
        assert zbx_srv_resp_data[ZBX_HDR_SIZE+zbx_srv_resp_body_len:] == b''

        if sys.version_info[0] >= 3:
            zbx_srv_resp_body = zbx_srv_resp_body.decode()
        # Return Zabbix Server answer as JSON
        return json.loads(zbx_srv_resp_body)

    def _socket_reset(self):
        if self.socket:
            self.socket.close()
            self.socket = None

    def _socket(self):
        # If socket already exists, use it
        if self.socket is not None:
            return self.socket

        # If not, we have to create it
        socket.setdefaulttimeout(self._zbx_config.timeout)
        # Connect to Zabbix server or proxy with provided config options
        try:
            _raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _raw_socket.connect(
                (self._zbx_config.server_active, self._zbx_config.server_port)
            )
        except:
            # If fail, connection refused error for example, destroy socket
            _rawsocket = None

        # Manage SSL context & wrapper
        ssl_context = None
        # TLS is enabled, let's set it up
        if self._zbx_config.tls_connect != 'unencrypted':
            from ssl import CertificateError, SSLError
            # Create a SSLContext and configure it
            ssl_context = ssl.SSLContext()

            # If provided, use cert file & key for client authentication
            if self._config.tls_cert_file and self._config.tls_key_file:
                ssl_context.load_cert_chain(
                    self._config.tls_cert_file,
                    self._config.tls_key_file
                )

            # If provided, use CA file & enforce server certificate chek
            if self._config.tls_ca_file:
                ssl_context.verify_mode = ssl.CERT_REQUIRED
                ssl_context.load_verify_locations(
                    cafile = self._config.tls_ca_file
                )

            ## If provided enforce server cert issuer check
            #if self._config.tls_server_cert_issuer:
            #    ssl_context.verify_issuer
            ## If provided enforce server cert subject check
            #if self._config.tls_server_cert_issuer:
            #    ssl_context.verify_issuer

            try:
                if isinstance(ssl_context, ssl.SSLContext):
                    _raw_socket = ssl_context.wrap_socket(_raw_socket, server_hostname=host)
            except CertificateError as e:
                raise errors.ConnectionError('SSL: ' + e.message)
            except SSLError as e:
                raise errors.ConnectionError('SSL: ' + e.reason)

        self.socket = _raw_socket
        return self.socket
