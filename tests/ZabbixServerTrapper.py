#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import struct
import datetime

try: import simplejson as json
except ImportError: import json

try: from thread import * # python 2
except ImportError: from _thread import * # python 3

if sys.version_info < (3,): # python 2
    def b(x):
        return x
else: # python 3
    import codecs
    def b(x):
        return codecs.utf_8_encode(x)[0]


REGISTERED_ITEMS = {
    "myhost1": {
        "my.zabbix.item1": 0,
        "my.zabbix.item2": "item string"
    },
    "myhost2": {
        "my.zabbix.item1": 0,
        "my.zabbix.item2": "item string"
    }
}

REGISTERED_LLD_ITEMS = {
    'myhost1': {
        'my.zabbix.lld_item1': [
            { '{#ZBX_LLD_KEY11}': 0,
              '{#ZBX_LLD_KEY12}': 'lld string' },
            { '{#ZBX_LLD_KEY11}': 1,
              '{#ZBX_LLD_KEY12}': 'another lld string' }
        ]
    },
    'myhost2': {
        'my.zabbix.lld_item2': [
            { '{#ZBX_LLD_KEY21}': 10,
              '{#ZBX_LLD_KEY21}': 'yet an lld string' },
            { '{#ZBX_LLD_KEY21}': 2,
              '{#ZBX_LLD_KEY21}': 'yet another lld string' }
        ]
    }
}

class ZabbixServer(object):
      class Trapper(object):
          HOST = '127.0.0.1'
          PORT = 10051
          ZBX_HDR = "ZBXD\1"

          def _parse_payload(self, payload):
              processed = 0
              failed = 0
              total = 0
              payload = json.loads(payload)
              data_list  = payload['data']
              for data in data_list:
                  total +=1
                  host = data['host']
                  key = data['key']
                  value = data['value']
                  try:
                      # We have an "LLD" value
                      item = json.loads(value)
                  except:
                      # We have an "item" value
                      if host not in REGISTERED_ITEMS:
                          failed += 1
                          break
                      if key not in REGISTERED_ITEMS[host]:
                          failed += 1
                          break
                      if value != REGISTERED_ITEMS[host][key]:
                          failed += 1
                          break
                      processed += 1
                      pass
              return processed, failed, total

          def _get_request(self):
              payload_body = ''
              output = ''
              # Send payload to Zabbix Server and check response header
              try:
                  # Check the 5 first bytes from answer
                  # to ensure it's well formatted
                  clt_hdr = self._conn.recv(5)
                  output = clt_hdr
                  assert(clt_hdr == b(self.ZBX_HDR))
                  # Get the 8 next bytes and unpack
                  # to get response's payload length
                  payload_hdr = self._conn.recv(8)
                  output += payload_hdr
                  payload_len = struct.unpack('<Q', payload_hdr)[0]
                  # Get response payload from Zabbix Server
                  payload_body = self._conn.recv(payload_len).decode('ASCII')
              except:
                  # We don't have Zabbix Header which seems to be OK
                  # Let's try without Zabbix Header
                  payload_body = ''
                  pass
              if not payload_body:
                  while True:
                      # Get data from connection
                      output += self._conn.recv(1024)
                      if len(output)<1024:
                          # If last received piece of data is shorter
                          # than buffer size, we're done
                          break
                  payload_body = output.decode('ASCII')
              return payload_body

          def _answer_request(self,result):
              data = json.dumps(result)
              # Build Zabbix Sender payload
              data_length = len(data)
              data_header = struct.pack('<Q', data_length)
              packet = b(self.ZBX_HDR) + data_header + b(data)
              # Send payload to Zabbix Server and check response header
              try:
                  self._conn.send(packet)
              except:
                  raise Exception('Error while sending answer to client')

          # Function for handling connections.
          # This will be used to create client threads
          def _clientthread(self):
              start_time = datetime.datetime.now().microsecond
              try:
                  payload = self._get_request()
              except:
                  self._conn.close()
                  raise Exception('Error while receiveing data')

              # We got payload, let's play with it
              result = "success"
              info = "processed: %d; failed: %d; total: %d; seconds spent: %f"              
              try:
                  processed, failed, total = self._parse_payload(payload)
                  stop_time = datetime.datetime.now().microsecond
                  time = stop_time - start_time
                  info = info % ( processed,
                                  failed,
                                  total,
                                  float(time)/1000000)
              except Exception as e:
                  result = "failed"
                  info   = str(e)
                  pass

              result = {
                  "response":result,
                  "info": info
              }
              # And send back the answer to the client
              self._answer_request(result)
              # End of play, let's close connection
              self._conn.close()

          def run(self):
              #socket.setdefaulttimeout(10)
              self.srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
              #Bind socket to local host and port
              try:
                  self.srv_sock.bind((self.HOST, self.PORT))
              except socket.error as msg:
                  print (('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]))
                  sys.exit()
              # Start listening on socket
              self.srv_sock.listen(10)
              # Now keep talking with the client
              while 1:
                  #wait to accept a connection - blocking call
                  self._conn, addr = self.srv_sock.accept()
                  print (('Connected with ' + addr[0] + ':' + str(addr[1])))
                  start_new_thread(self._clientthread ,())
              self.srv_sock.close()

ZabbixServer.Trapper().run()
