# python-zabbix

Very simple python module implementing Zabbix Sender protocol.  
It allows one to build list of items and send them as trapper.
It currently supports `items` as well as [`Low Level Discovery`](https://www.zabbix.com/documentation/2.4/manual/discovery/low_level_discovery).

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
zbx_container = zabbix.DataContainer("items", "localhost", 10051)

''' set debug '''
zbx_container.set_debug(True)
zbx_container.set_verbosity(True)

''' Add items one after the other '''
hostname="myhost"    item="my.zabbix.item"
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
ret = zbx_container.send(zbx_container)
''' If returns False, then we got a problem '''
if not ret:
    print "Ooops. Something went wrong when sending data to Zabbix"

print "Everything is OK"
```

## Send Low Level Discovery as trappers

```python
#!/usr/bin/env python

''' import module '''
import protobix

''' create DataContainer, providing data_type, zabbix server and port '''
zbx_container = zabbix.DataContainer("lld", "localhost", 10051)

''' set debug '''
zbx_container.set_debug(True)
zbx_container.set_verbosity(True)

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
            { 'my.zabbix.ldd_key1': 0,
              'my.zabbix.ldd_key2': 'lld string' },
            { 'my.zabbix.ldd_key3': 1,
              'my.zabbix.ldd_key4': 'another lld string' }
        ]
    'myhost2':
        'my.zabbix.lld_item2': [
            { 'my.zabbix.ldd_key10': 10,
              'my.zabbix.ldd_key20': 'yet an lld string' },
            { 'my.zabbix.ldd_key30': 2,
              'my.zabbix.ldd_key40': 'yet another lld string' }
        ]
}
zbx_container.add(data)

''' Send data to zabbix '''
ret = zbx_container.send(zbx_container)
''' If returns False, then we got a problem '''
if not ret:
    print "Ooops. Something went wrong when sending data to Zabbix"

print "Everything is OK"
```

## How to contribute

Clone this repository, make your modifications into a dedicated branch and ask for a pull request against `upstream` branch.

__Do not use master_ as reference since master includes `Debian` packaging stuff.
