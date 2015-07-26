import logging
import re
import simplejson
import socket
import struct
import time
import sys

from .senderexception import SenderException

ZBX_HDR = "ZBXD\1%s%s"
ZBX_HDR_SIZE = 13
# For both 2.0 & >2.2 Zabbix version
# 2.0: Processed 0 Failed 1 Total 1 Seconds spent 0.000057
# 2.2: processed: 50; failed: 1000; total: 1050; seconds spent: 0.09957
# 2.4: processed: 50; failed: 1000; total: 1050; seconds spent: 0.09957
ZBX_RESP_REGEX = r'[Pp]rocessed:? (\d+);? [Ff]ailed:? (\d+);? [Tt]otal:? (\d+);? [Ss]econds spent:? (\d+\.\d+)'
ZBX_DBG_SEND_RESULT = "Send result [%s-%s-%s] for [%s %s %s]"

def recv_all(sock):
    buf = ''
    while len(buf)<ZBX_HDR_SIZE:
        chunk = sock.recv(ZBX_HDR_SIZE-len(buf))
        if not chunk:
            return buf
        buf += chunk
    return buf

class SenderProtocol(object):

    def __init__(self, zbx_host,
                       zbx_port,
                       debug     = False,
                       dryrun    = False):
        self._debug     = debug
        self._dryrun    = dryrun
        self._zbx_host  = zbx_host
        self._zbx_port  = zbx_port

    @property
    def zbx_host(self):
        return self._zbx_host

    @zbx_host.setter
    def zbx_host(self, value):
        self._zbx_host = value

    @property
    def zbx_port(self):
        return self._zbx_port

    @zbx_port.setter
    def zbx_port(self, value):
        self._zbx_port = value

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        if value in [True, False]:
            self._debug = value
        else:
            raise ValueError('debug parameter requires boolean')

    @property
    def dryrun(self):
        return self._dryrun

    @dryrun.setter
    def dryrun(self, value):
        if value in [True, False]:
            self._dryrun = value
        else:
            raise ValueError('dryrun parameter requires boolean')

    @property
    def result(self):
        return self._result

    def send_to_zabbix(self, data):
        socket.setdefaulttimeout(1)

        data_length = len(data)
        data_header = struct.pack('<Q', data_length)
        packet = ZBX_HDR % (data_header, data)
        try:
            zbx_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            zbx_sock.connect((self.zbx_host, int(self.zbx_port)))
        except:
            # Maybe we could consider storing missed sent data for later retry
            self._items_list = []
            zbx_sock.close()
            raise SenderException('Connection to Zabbix failed')


        try:
            zbx_sock.sendall(packet)
            zbx_srv_resp_hdr = recv_all(zbx_sock)
            zbx_srv_resp_body_len = struct.unpack('<Q', zbx_srv_resp_hdr[5:])[0]
            zbx_srv_resp_body = zbx_sock.recv(zbx_srv_resp_body_len)
            zbx_sock.close()
        except:
            self._items_list = []
            zbx_sock.close()
            if not zbx_srv_resp_hdr.startswith(ZBX_HDR) or len(zbx_srv_resp_hdr) != ZBX_HDR_SIZE:
                raise SenderException('Wrong Zabbix response')
            else:
                raise SenderException('Error while sending data to Zabbix')

        return simplejson.loads(zbx_srv_resp_body)

    def send(self):
        zbx_answer = 0
        self._result = []

        if self.debug:
            self.single_send()
        else:
            self.bulk_send()
        self._items_list = []

    def bulk_send(self):
        data = simplejson.dumps({ "data": self._items_list,
                                  "request": self.REQUEST,
                                  "clock": self.clock })
        if not self._dryrun:
            zbx_answer = self.send_to_zabbix(data)
            result = re.findall( ZBX_RESP_REGEX, zbx_answer.get('info'))
            result = result[0]
            self._result.append(result)
        else:
            self._result.append(['0', '0', str(len(self._items_list))])

    def single_send(self):
        for item in self._items_list:
            data = simplejson.dumps({ "data": [ item ],
                                      "request": self.REQUEST,
                                      "clock": self.clock })
            if not self._dryrun: 
                zbx_answer = self.send_to_zabbix(data)
                result = re.findall( ZBX_RESP_REGEX, zbx_answer.get('info'))
                result = result[0]
                self._result.append(result)
            else:
                result = ['0', '0', '1']
                self._result.append(result)

            if self.debug:
                print((
                    ZBX_DBG_SEND_RESULT % (result[0],
                                           result[1],
                                           result[2],
                                           item["host"],
                                           item["key"],
                                           item["value"])))