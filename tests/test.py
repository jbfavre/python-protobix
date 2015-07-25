#!/usr/bin/env python

# -*- coding: utf-8 -*-

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import protobix

def test01(zbx_container):
  data = {
      "myhost1": {
          "my.zabbix.item1": 0,
          "my.zabbix.item2": "item string"
      },
      "myhost2": {
          "my.zabbix.item1": 0,
          "my.zabbix.item2": "item string"
      }
  }
  zbx_container.add(data)

  ''' Send data to zabbix '''
  ret = zbx_container.send()
  return ret

def test02(zbx_container):
  data = {
      "myhost1": {
          "my.zabbix.item1": 0,
          "my.zabbix.item2": "item string"
      },
      "myhost2": {
          "my.zabbix.item1": 0,
          "my.zabbix.item2": "item string"
      }
  }
  zbx_container.add(data)

  ''' Send data to zabbix '''
  ret = zbx_container.send()
  return ret

def test03(zbx_container):
  data = {
      "myhost1": {
          "my.zabbix.item1": 0,
          "my.zabbix.item2": "item string"
      },
      "myhost2": {
          "my.zabbix.item1": 0,
          "my.zabbix.item2": "item string"
      }
  }
  zbx_container.add(data)

  ''' Send data to zabbix '''
  ret = zbx_container.send()
  return ret, len(zbx_container.get_items_list())




''' create DataContainer, providing data_type, zabbix server and port '''
zbx_container = protobix.DataContainer("items", "localhost", 10051)
zbx_container.set_debug(False)
zbx_container.set_verbosity(False)

print "\nTest 1: best case scenario"
try:
  ret = ''
  ret = test01(zbx_container)
  print "      : should not fail. OK"
  print "      : %s" % ret
except:
  print "      : should not fail. NOK" 
  print "      : %s" % ret

print "\nTest 2: connection to Zabbix server fail (use of non binded port 10052)"
try:
  ret = ''
  zbx_container.set_port(10052)
  ret = test02(zbx_container)
  print "      : should fail. NOK" 
except:
  print "      : should fail. OK" 
  print "      :  %s" % ret

print "\nTest 3: check that Datacontainer got emptied after first successful sent"
try:
  ret = ''
  zbx_container.set_port(10051)
  ret, nb_item = test03(zbx_container)
  if nb_item:
    raise ValueError("Got %d items it items_list" % nb_item)
  print "      : should not fail. OK - %s - %d" % (ret, nb_item)
except Exception, e:
  print "      : should not fail. NOK - " + str(e)
