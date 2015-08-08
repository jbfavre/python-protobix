#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import struct
import datetime
import logging

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
                self.logger.debug(
                    'Parsing payload ' + str(total) +
                    ' with host: ' + host +
                    ' and key: ' + key
                )
                try:
                    # Try as we had an "LLD" value
                    item = json.loads(value)
                    self.logger.debug('        payload ' + str(total) + ' is LLD')
                    if host not in REGISTERED_LLD_ITEMS or \
                       key not in REGISTERED_LLD_ITEMS[host]:
                        self.logger.debug('        host or key not registered')
                        failed += 1
                        continue
                    processed += 1
                except:
                    self.logger.debug('        payload ' + str(total) + ' is item')
                    # We have an "item" value
                    if host not in REGISTERED_ITEMS or \
                       key not in REGISTERED_ITEMS[host] or \
                       value != REGISTERED_ITEMS[host][key]:
                        self.logger.error(
                            '        host or key not registered' + 
                            ' or incorrect value'
                        )
                        failed += 1
                        continue
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
                self.logger.debug('Got ZBX header')
                # Get the 8 next bytes and unpack
                # to get response's payload length
                payload_hdr = self._conn.recv(8)
                output += payload_hdr
                payload_len = struct.unpack('<Q', payload_hdr)[0]
                # Get response payload from Zabbix Server
                payload_body = self._conn.recv(payload_len).decode('ASCII')
            except:
                self.logger.debug("Did not get ZBX header. Ok, let's try anyway")
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
                self.logger.error('Error while sending answer to client')
                raise Exception('Error while sending answer to client')

        def _clientthread(self):
            start_time = datetime.datetime.now().microsecond
            try:
                self.logger.info('Receiving request')
                payload = self._get_request()
            except:
                self._conn.close()
                self.logger.error('Error while receiveing data')
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
                self.logger.info('Processed ' + str(total) + ' items, ' +
                                 str(processed) + ' OK, ' + str(failed) +
                                 ' failed in ' + str(float(time)/1000000) + 's')
            except Exception as e:
                self.logger.error('Payload parsing failed')
                # For some reason, we failed parsing payload.
                # Will answer wih a failed trapper json struct.
                result = "failed"
                info   = str(e)
                pass

            result = {
                "response":result,
                "info": info
            }
            self.logger.debug(result)
            # And send back the answer to the client
            self._answer_request(result)
            # End of play, let's close connection
            self._conn.close()

        def _setup_logging(self):
            common_log_format = '[%(name)s:%(levelname)s] %(message)s'
            # Enable default console logging
            consoleHandler = logging.StreamHandler()
            consoleFormatter = logging.Formatter(
                fmt = common_log_format,
                datefmt = '%Y%m%d:%H%M%S'
            )
            consoleHandler.setFormatter(consoleFormatter)
            self.logger.addHandler(consoleHandler)
            self.logger.setLevel(logging.DEBUG)

        def run(self):
            self.logger = logging.getLogger(self.__class__.__name__)
            self._setup_logging()
            self.logger.debug('Initialized ZabbixTrapper server')
            self.srv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Avoid bind: adress already in use error
            # Reuse addr+port socket except if a process listens on it
            self.srv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            #Bind socket to local host and port
            try:
                self.logger.debug('Trying to bind ' + self.HOST + ':' + str(self.PORT))
                self.srv_sock.bind((self.HOST, self.PORT))
            except socket.error as msg:
                self.logger.error(
                    'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
                )
                sys.exit()
            self.logger.debug('Starts listening on ' + self.HOST + ':' + str(self.PORT))
            # Start listening on socket
            self.srv_sock.listen(10)
            # Now keep talking with the client
            while 1:
                #wait to accept a connection - blocking call
                self._conn, addr = self.srv_sock.accept()
                self.logger.debug(
                    'Connected with ' + addr[0] + ':' + str(addr[1])
                )
                start_new_thread(self._clientthread ,())
            self.srv_sock.close()

ZabbixServer.Trapper().run()