import logging
import re
import simplejson
import socket
import struct
import time

from senderexception import SenderException

ZBX_HDR = "ZBXD\1"
ZBX_HDR_SIZE = 13
# For both 2.0 & >2.2 Zabbix version
# 2.0: Processed 0 Failed 1 Total 1 Seconds spent 0.000057
# 2.2: processed: 50; failed: 1000; total: 1050; seconds spent: 0.09957
# 2.4: processed: 50; failed: 1000; total: 1050; seconds spent: 0.09957
ZBX_RESP_REGEX = r'[Pp]rocessed:? (\d+);? [Ff]ailed:? (\d+);? [Tt]otal:? (\d+);? [Ss]econds spent:? (\d+\.\d+)'
ZBX_DBG_SEND_RESULT = "DBG - Send result [%s-%s-%s-%s] for [%s %s %s]"

def recv_all(sock):
    buf = ''
    while len(buf)<ZBX_HDR_SIZE:
        chunk = sock.recv(ZBX_HDR_SIZE-len(buf))
        if not chunk:
            return buf
        buf += chunk
    return buf

class SenderProtocol(object):

    def __init__(self, zbx_host="", zbx_port=10051):
        self.debug = False
        self.verbosity = False
        self.dryrun = False
        self.request = ""
        self.zbx_host = zbx_host
        self.zbx_port = zbx_port
        self.data_container = ""

    def set_host(self, zbx_host):
        self.zbx_host = zbx_host

    def set_port(self, zbx_port):
        self.zbx_port = zbx_port

    def set_verbosity(self, verbosity):
        self.verbosity = verbosity

    def set_debug(self, debug):
        self.debug = debug

    def set_dryrun(self, dryrun):
        self.dryrun = dryrun

    def __repr__(self):
        return simplejson.dumps({ "data": ("%r" % self.items_list),
                                  "request": self.request,
                                  "clock": int(time.time()) })

    def send_to_zabbix(self, data):
        data_len =  struct.pack('<Q', len(data))
        packet = ZBX_HDR + data_len + data

        try:
            zbx_sock = socket.socket()
            zbx_sock.connect((self.zbx_host, int(self.zbx_port)))
            zbx_sock.sendall(packet)
        except (socket.gaierror, socket.error) as e:
            # Maybe we could consider storing missed sent data for later retry
            self.items_list = []
            zbx_sock.close()
            raise SenderException(e[1])
        else:
            try:
                zbx_srv_resp_hdr = recv_all(zbx_sock)
                zbx_srv_resp_body_len = struct.unpack('<Q', zbx_srv_resp_hdr[5:])[0]
                zbx_srv_resp_body = zbx_sock.recv(zbx_srv_resp_body_len)
                zbx_sock.close()
            except:
                zbx_sock.close()
                if not zbx_srv_resp_hdr.startswith(ZBX_HDR) or len(zbx_srv_resp_hdr) != ZBX_HDR_SIZE:
                    raise SenderException("Wrong zabbix response")
                else:
                    raise SenderException("Error while sending data to Zabbix")

        return simplejson.loads(zbx_srv_resp_body)

    def send(self):
        if self.debug:
            zbx_answer = self.single_send()
        else:
            zbx_answer = self.bulk_send()
        self.items_list = []
        return zbx_answer

    def bulk_send(self):
        data = simplejson.dumps({ "data": self.items_list,
                                  "request": self.request,
                                  "clock": int(time.time()) })
        zbx_answer = self.send_to_zabbix(data)
        if self.verbosity:
            print zbx_answer.get('info')
        return zbx_answer

    def single_send(self):
        for item in self.items_list:
            data = simplejson.dumps({ "data": [ item ],
                                      "request": self.request,
                                      "clock": int(time.time()) })
            zbx_answer = 0
            if not self.dryrun:
                zbx_answer = self.send_to_zabbix(data)
                result = re.findall( ZBX_RESP_REGEX, zbx_answer.get('info'))
                result = result[0]

            if self.debug:
                print (ZBX_DBG_SEND_RESULT % (result[0],
                                              result[1],
                                              result[2],
                                              result[3],
                                              item["host"],
                                              item["key"],
                                              item["value"]))
        return zbx_answer
