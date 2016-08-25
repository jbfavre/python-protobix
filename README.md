# python-protobix

* dev Branch: [![Build Status](https://travis-ci.org/jbfavre/python-protobix.svg?branch=dev)](https://travis-ci.org/jbfavre/python-protobix)
* upstream Branch (default): [![Build Status](https://travis-ci.org/jbfavre/python-protobix.svg?branch=upstream)](https://travis-ci.org/jbfavre/python-protobix)

`python-protobix` is a very simple python module implementing [Zabbix Sender protocol 2.0](https://www.zabbix.org/wiki/Docs/protocols/zabbix_sender/2.0).  
It allows to build list of Zabbix items and send them as trappers.

Currently `python-protobix` supports `items` as well as [`Low Level Discovery`](https://www.zabbix.com/documentation/2.4/manual/discovery/low_level_discovery).

Please note that `python-protobix` is developped and tested on Debian GNU/Linux only.  
I can't enforce compatibility with other distributions, though it should work on any distribution providing Python 2.7 or Python 3.x.

Any feedback on this is, of course, welcomed.

## Test

To install all required dependencies and launch test suite

    python setup.py test

By default, all tests named like `*need_backend*` are disabled, since they need a working Zabbix Server.

If you want to run theses tests as well, you will need:
* a working Zabbix Server 3.x configuration file like the one in `tests/zabbix/zabbix_server.conf`
* SQL statements in `tests/zabbix/zabbix_server_mysql.sql` with all informations to create testing  hosts & items

You can then start Zabbix Server with `zabbix_server -c tests/zabbix/zabbix_server.conf -f` and launch test suite with

    py.test --cov protobix --cov-report term-missing

### Using a docker container

You can also use docker to run test suite on any Linux distribution of your choice.  
You can use provided script `docker-tests.sh` as entrypoint example:

    docker run --volume=$(pwd):/home/python-protobix --entrypoint=/home/python-protobix/tests/docker-tests.sh -ti debian:jessie

__Please note that this docker entrypoint does not provide a way to execute test that need a backend__.

## Installation

With `pip` (stable version):

    pip install protobix

With `pip` (test version):

    pip install -i https://testpypi.python.org/simple/ protobix

Python is available as Debian package for Debian GNU/Linux sid and testing.

## Usage

Once module is installed, you can use it as follow

### Extends `protobix.SampleProbe`

`python-protobix` provides a convenient sample probe you can extend to fit your own needs.

Using `protobix.SampleProbe` allows you to concetrate on getting metrics or Low Level Discovery items without taking care of anything related to `protobix` itself.  
This is the recommanded way of using `python-protobix`.

`protobix.SampleProbe` provides a `run` methods which take care of everything related to `protobix`.

Some probes are available from my Github repository [`python-zabbix`](https://github.com/jbfavre/python-zabbix)

### Send items as trappers

```python
#!/usr/bin/env python

''' import module '''
import protobix

DATA = {
    "protobix.host1": {
        "my.protobix.item.int": 0,
        "my.protobix.item.string": "item string"
    },
    "protobix.host2": {
        "my.protobix.item.int": 0,
        "my.protobix.item.string": "item string"
    }
}

zbx_datacontainer = protobix.DataContainer()
zbx_datacontainer.data_type = 'lld'
zbx_datacontainer.add(DATA)
zbx_datacontainer.send()
```

### Send Low Level Discovery as trappers

```python
#!/usr/bin/env python

''' import module '''
import protobix

DATA = {
    'protobix.host1': {
        'my.protobix.lld_item1': [
            { '{#PBX_LLD_KEY11}': 0,
              '{#PBX_LLD_KEY12}': 'lld string' },
            { '{#PBX_LLD_KEY11}': 1,
              '{#PBX_LLD_KEY12}': 'another lld string' }
        ],
        'my.protobix.lld_item2': [
            { '{#PBX_LLD_KEY21}': 10,
              '{#PBX_LLD_KEY21}': 'yet an lld string' },
            { '{#PBX_LLD_KEY21}': 2,
              '{#PBX_LLD_KEY21}': 'yet another lld string' }
        ]
    },
    'protobix.host2': {
        'my.protobix.lld_item1': [
            { '{#PBX_LLD_KEY11}': 0,
              '{#PBX_LLD_KEY12}': 'lld string' },
            { '{#PBX_LLD_KEY11}': 1,
              '{#PBX_LLD_KEY12}': 'another lld string' }
        ],
        'my.protobix.lld_item2': [
            { '{#PBX_LLD_KEY21}': 10,
              '{#PBX_LLD_KEY21}': 'yet an lld string' },
            { '{#PBX_LLD_KEY21}': 2,
              '{#PBX_LLD_KEY21}': 'yet another lld string' }
        ]
    }
}

zbx_datacontainer = protobix.DataContainer()
zbx_datacontainer.data_type = 'lld'
zbx_datacontainer.add(DATA)
zbx_datacontainer.send()
```

### Advanced configuration

`python-protobix` behaviour can be altered in many ways using options.  
All configuration options are stored in a `protobix.ZabbixAgentConfig` instance.

__Protobix specific configuration options__

| option name  | Default value | ZabbixAgentConfig property | Command-line option (SampleProbe) |
|:------------:|:-------------:|:--------------------------:|:---------------------------------:|
| data_type    | `None`        | data_type                  | `--update-items` or `--discovery` |
| dryrun       | `False`       | dryrun                     | `-d` or `--dryrun`                |

__Zabbix Agent configuration options__

| option name          | Default value           | ZabbixAgentConfig property | Command-line option (SampleProbe) |
|:--------------------:|:-----------------------:|:--------------------------:|:---------------------------------:|
| ServerActive         | 127.0.0.1               | server_active              | `-z` or `--zabbix-server`         |
| ServerPort           | 10051                   | server_port                | `-p` or `--port`                  |
| LogType              | file                    | log_type                   | none                              |
| LogFile              | /tmp/zabbix_agentd.log  | log_file                   | none                              |
| DebugLevel           | 3                       | debug_level                | `-v` (from none to `-vvvvv`)      |
| Timeout              | 3                       | timeout                    | none                              |
| Hostname             | `socket.getfqdn()`      | hostname                   | none                              |
| TLSConnect           | unencrypted             | tls_connect                | `--tls-connect`                   |
| TLSCAFile            | `None`                  | tls_ca_file                | `--tls-ca-file`                   |
| TLSCertFile          | `None`                  | tls_cert_file              | `--tls-cert-file`                 |
| TLSCRLFile           | `None`                  | tls_crl_file               | `--tls-crl-file`                  |
| TLSKeyFile           | `None`                  | tls_key_file               | `--tls-key-file`                  |
| TLSServerCertIssuer  | `None`                  | tls_server_cert_issuer     | `--tls-server-cert-issuer`        |
| TLSServerCertSubject | `None`                  | tls_server_cert_subject    | `--tls-server-cert-subject`       |

## Contribute

You can contribute to `protobix`:
* fork this repository
* write tests and documentation
* implement the feature you need
* open a pull request against __`upstream`__ branch
