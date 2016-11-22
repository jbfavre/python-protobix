import struct
import sys
import time
import re

import socket
try: import simplejson as json
except ImportError: import json # pragma: no cover

from .zabbixagentconfig import ZabbixAgentConfig

if sys.version_info < (3,): # pragma: no cover
    def b(x):
        return x
else: # pragma: no cover
    import codecs
    def b(x):
        return codecs.utf_8_encode(x)[0]

HAVE_DECENT_SSL = False
if sys.version_info > (2,7,9):
    import ssl
    # Zabbix force TLSv1.2 protocol
    # in src/libs/zbxcrypto/tls.c function zbx_tls_init_child
    ZBX_TLS_PROTOCOL=ssl.PROTOCOL_TLSv1_2
    HAVE_DECENT_SSL = True

ZBX_HDR = "ZBXD\1"
ZBX_HDR_SIZE = 13
ZBX_RESP_REGEX = r'[Pp]rocessed:? (\d+);? [Ff]ailed:? (\d+);? ' + \
                 r'[Tt]otal:? (\d+);? [Ss]econds spent:? (\d+\.\d+)'

class SenderProtocol(object):

    REQUEST = "sender data"
    _logger = None

    def __init__(self, logger=None):
        self._config = ZabbixAgentConfig()
        self._items_list = []
        self.socket = None
        if logger: # pragma: no cover
            self._logger = logger

    @property
    def server_active(self):
        return self._config.server_active

    @server_active.setter
    def server_active(self, value):
        if self._logger: # pragma: no cover
            self._logger.debug(
                "Replacing server_active  '%s' with '%s'" %
                (self._config.server_active, value)
            )
        self._config.server_active = value

    @property
    def server_port(self):
        return self._config.server_port

    @server_port.setter
    def server_port(self, value):
        if self._logger: # pragma: no cover
            self._logger.debug(
                "Replacing server_port  '%s' with '%s'" %
                (self._config.server_port, value)
            )
        self._config.server_port = value

    @property
    def debug_level(self):
        return self._config.debug_level

    @debug_level.setter
    def debug_level(self, value):
        if self._logger: # pragma: no cover
            self._logger.debug(
                "Replacing debug_level  '%s' with '%s'" %
                (self._config.debug_level, value)
            )
        self._config.debug_level = value

    @property
    def items_list(self):
        return self._items_list

    @property
    def clock(self):
        return int(time.time())

    def _send_to_zabbix(self, item):
        if self._logger: # pragma: no cover
            self._logger.info(
                "Send data to Zabbix Server"
            )

        # Format data to be sent
        if self._logger: # pragma: no cover
            self._logger.debug(
                "Building packet to be sent to Zabbix Server"
            )
        payload = json.dumps({"data": item,
                              "request": self.REQUEST,
                              "clock": self.clock })
        if self._logger: # pragma: no cover
            self._logger.debug('About to send: ' + str(payload))
        data_length = len(payload)
        data_header = struct.pack('<Q', data_length)
        packet = b(ZBX_HDR) + data_header + b(payload)
        if self._logger: # pragma: no cover
            self._logger.debug(
                "Sending packet to Zabbix Server"
            )
        # Send payload to Zabbix Server
        self._socket().sendall(packet)

    def _read_from_zabbix(self):
        recv_length = 4096
        zbx_srv_resp_data = b''

        # Read Zabbix server answer
        if self._logger: # pragma: no cover
            self._logger.info(
                "Reading Zabbix Server's answer"
            )
        while recv_length >= 4096:
            _buffer = self._socket().recv(4096)
            zbx_srv_resp_data += _buffer
            recv_length = len(_buffer)

        _buffer = None
        recv_length = None
        # Check that we have a valid Zabbix header mark
        if self._logger: # pragma: no cover
            self._logger.debug(
                "Checking Zabbix headers"
            )
        assert zbx_srv_resp_data[:5] == b(ZBX_HDR)

        # Extract response body length from packet
        zbx_srv_resp_body_len = struct.unpack('<Q', zbx_srv_resp_data[5:ZBX_HDR_SIZE])[0]

        # Extract response body
        if self._logger: # pragma: no cover
            self._logger.debug(
                "Extracting answer's body"
            )
        body_offset=ZBX_HDR_SIZE+zbx_srv_resp_body_len
        zbx_srv_resp_body = zbx_srv_resp_data[ZBX_HDR_SIZE:body_offset]

        # Check that we have read the whole packet
        assert zbx_srv_resp_data[body_offset:] == b''

        if self._logger: # pragma: no cover
            self._logger.debug(
                "Building JSON object to be analyzed"
            )
        if sys.version_info[0] >= 3: # pragma: no cover
            zbx_srv_resp_body = zbx_srv_resp_body.decode()
        # Analyze Zabbix answer
        response, processed, failed, total, time = self._handle_response(zbx_srv_resp_body)

        # Return Zabbix Server answer as JSON
        return response, processed, failed, total, time

    def _handle_response(self, zbx_answer):
        """
        Analyze Zabbix Server response
        Returns a list with number of:
        * processed items
        * failed items
        * total items
        * time spent

        :zbx_answer: Zabbix server response as string
        """
        zbx_answer = json.loads(zbx_answer)
        if self._logger: # pragma: no cover
            self._logger.info(
                "Anaylizing Zabbix Server's answer"
            )
            if zbx_answer:
                self._logger.debug("Zabbix Server response is: [%s]" % zbx_answer)

        # Default items number in length of th storage list
        nb_item = len(self._items_list)
        if self._config.debug_level >= 4:
            # If debug enabled, force it to 1
            nb_item = 1

        # If dryrun is disabled, we can process answer
        response = zbx_answer.get('response')
        result = re.findall(ZBX_RESP_REGEX, zbx_answer.get('info'))
        processed, failed, total, time = result[0]

        return response, int(processed), int(failed), int(total), float(time)

    def _socket_reset(self):
        if self.socket:
            if self._logger: # pragma: no cover
                self._logger.info(
                    "Reset socket"
                )
            self.socket.close()
            self.socket = None

    def _socket(self):
        # If socket already exists, use it
        if self.socket is not None:
            if self._logger: # pragma: no cover
                self._logger.debug(
                    "Using existing socket"
                )
            return self.socket

        # If not, we have to create it
        if self._logger: # pragma: no cover
            self._logger.debug(
                "Setting socket options"
            )
        socket.setdefaulttimeout(self._config.timeout)
        # Connect to Zabbix server or proxy with provided config options
        if self._logger: # pragma: no cover
            self._logger.info(
                "Creating new socket"
            )
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # TLS is enabled, let's set it up
        if self._config.tls_connect != 'unencrypted' and HAVE_DECENT_SSL is True:
            if self._logger: # pragma: no cover
                self._logger.info(
                    'Configuring TLS to %s' % str(self._config.tls_connect)
                )
            # Setup TLS context & Wrap socket
            self.socket = self._init_tls()
            if self._logger: # pragma: no cover
                self._logger.info(
                    'Network socket initialized with TLS support'
                )

        if self._logger and isinstance(self.socket, socket.socket): # pragma: no cover
            self._logger.info(
                'Network socket initialized with no TLS'
            )
        # Connect to Zabbix Server
        self.socket.connect(
            (self._config.server_active, self._config.server_port)
        )
        #if isinstance(self.socket, ssl.SSLSocket):
        #    server_cert = self.socket.getpeercert()
        #    if self._config.tls_server_cert_issuer:
        #        print(server_cert['issuer'])
        #        assert server_cert['issuer'] == self._config.tls_server_cert_issuer
        #        self._logger.info(
        #            'Server certificate issuer is %s' %
        #            server_cert['issuer']
        #        )
        #    if self._config.tls_server_cert_subject:
        #        print(server_cert['subject'])
        #        assert server_cert['subject'] == self._config.tls_server_cert_subject
        #        self._logger.info(
        #            'Server certificate subject is %s' %
        #            server_cert['subject']
        #        )

        return self.socket

    """
    Manage TLS context & Wrap socket
    Returns ssl.SSLSocket if TLS enabled
            socket.socket if TLS disabled
    """
    def _init_tls(self):
        # Create a SSLContext and configure it
        if self._logger: # pragma: no cover
            self._logger.info(
                "Initialize TLS context"
            )
        ssl_context = ssl.SSLContext(ZBX_TLS_PROTOCOL)
        if self._logger: # pragma: no cover
            self._logger.debug(
                'Setting TLS verify_mode to ssl.CERT_REQUIRED'
            )
        ssl_context.verify_mode = ssl.CERT_REQUIRED

        # Avoid CRIME and related attacks
        if self._logger: # pragma: no cover
            self._logger.debug(
                'Setting TLS option ssl.OP_NO_COMPRESSION'
            )
        ssl_context.options |= ssl.OP_NO_COMPRESSION
        ssl_context.verify_flags =  ssl.VERIFY_X509_STRICT

        # If tls_connect is cert, we must provide client cert file & key
        if self._config.tls_connect == 'cert':
            if self._logger: # pragma: no cover
                self._logger.debug(
                    "Using provided TLSCertFile %s" % self._config.tls_cert_file
                )
                self._logger.debug(
                    "Using provided TLSKeyFile %s" % self._config.tls_key_file
                )
            ssl_context.load_cert_chain(
                self._config.tls_cert_file,
                self._config.tls_key_file
            )
        elif self._config.tls_connect == 'psk':
            raise NotImplementedError

        # If provided, use CA file & enforce server certificate chek
        if self._config.tls_ca_file:
            if self._logger: # pragma: no cover
                self._logger.debug(
                    "Using provided TLSCAFile %s" % self._config.tls_ca_file
                )
            ssl_context.load_default_certs(ssl.Purpose.SERVER_AUTH)
            ssl_context.load_verify_locations(
                cafile=self._config.tls_ca_file
            )

        # If provided, use CRL file & enforce server certificate check
        if self._config.tls_crl_file:
            if self._logger: # pragma: no cover
                self._logger.debug(
                    "Using provided TLSCRLFile %s" % self._config.tls_crl_file
                )
            ssl_context.verify_flags |=  ssl.VERIFY_CRL_CHECK_LEAF
            ssl_context.load_verify_locations(
                cafile=self._config.tls_crl_file
            )

        ## If provided enforce server cert issuer check
        #if self._config.tls_server_cert_issuer:
        #    verify_issuer

        ## If provided enforce server cert subject check
        #if self._config.tls_server_cert_issuer:
        #    verify_issuer

        # Once configuration is done, wrap network socket to TLS context
        tls_socket = ssl_context.wrap_socket(
            self.socket
        )
        assert isinstance(tls_socket, ssl.SSLSocket)
        return tls_socket
