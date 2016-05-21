# python-protobix

dev Branch: [![Build Status](https://travis-ci.org/jbfavre/python-protobix.svg?branch=dev)](https://travis-ci.org/jbfavre/python-protobix)
upstream Branch: [![Build Status](https://travis-ci.org/jbfavre/python-protobix.svg?branch=upstream)](https://travis-ci.org/jbfavre/python-protobix)

Very simple python module implementing Zabbix Sender protocol.  
It allows one to build list of items and send them as trapper.
It currently supports `items` as well as [`Low Level Discovery`](https://www.zabbix.com/documentation/2.4/manual/discovery/low_level_discovery).

## Test

First, launch provided Zabbix Trapper Server:

    python tests/ZabbixServerTrapper.py

Then, launch test suite:

    python setup.py test

## Install

With `pip`:

    pip install protobix

With `pip` (test version):

    pip install -i https://testpypi.python.org/simple/ protobix

Build `Debian` package:

    apt-get install python-stdeb python-setuptools

    cd module
    python setup.py --command-packages=stdeb.command bdist_deb
    apt-get install python-simplejson
    dpkg -i deb_dist/python-zabbix_0.0.1-1_all.deb

## Usage

Once module is installed, you can use it as follow

## Send items as trappers

```python
#!/usr/bin/env python

''' import module '''
import protobix

''' create DataContainer, providing data_type, zabbix server and port '''
zbx_container = protobix.DataContainer(data_type = "items",
                                       zbx_host  = '127.0.0.1',
                                       zbx_port  = 10051,
                                       debug     = False,
                                       dryrun    = False)
''' set debug '''
zbx_container.debug = True

''' set dryrun for testing purpose. Won't send anything to Zabbix '''
zbx_container.dryrun = True

''' Add items one after the other '''
hostname="myhost"
item="my.zabbix.item"
value=0
zbx_container.add_item( hostname, item, value)

''' or use bulk insert '''
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
try:
    zbx_container.send()
except SendException as e:
    print str(e)

print "Everything is OK"
```

## Send Low Level Discovery as trappers

```python
#!/usr/bin/env python

''' import module '''
import protobix

''' create DataContainer, providing data_type, zabbix server and port '''
zbx_container = protobix.DataContainer(data_type = "lld",
                                       zbx_host  = '127.0.0.1',
                                       zbx_port  = 10051,
                                       debug     = False,
                                       dryrun    = False)
''' set debug '''
zbx_container.debug = True

''' Add items one after the other '''
hostname="myhost"
item="my.zabbix.lld_item1"
value=[
    { 'my.zabbix.ldd_key1': 0,
      'my.zabbix.ldd_key2': 'lld string' },
    { 'my.zabbix.ldd_key3': 1,
      'my.zabbix.ldd_key4': 'another lld string' }
]
zbx_container.add_item( hostname, item, value)

''' or use bulk insert '''
data = {
    'myhost1': {
        'my.zabbix.lld_item1': [
            { '{#ZBX_LLD_KEY11}': 0,
              '{#ZBX_LLD_KEY12}': 'lld string' },
            { '{#ZBX_LLD_KEY11}': 1,
              '{#ZBX_LLD_KEY12}': 'another lld string' }
        ]
    'myhost2':
        'my.zabbix.lld_item2': [
            { '{#ZBX_LLD_KEY21}': 10,
              '{#ZBX_LLD_KEY21}': 'yet an lld string' },
            { '{#ZBX_LLD_KEY21}': 2,
              '{#ZBX_LLD_KEY21}': 'yet another lld string' }
        ]
}
zbx_container.add(data)

''' Send data to zabbix '''
try:
    zbx_container.send()
except SendException as e:
    print str(e)

print "Everything is OK"
```
