import configobj
import socket

class ZabbixAgentConfig(object):

    _logger = None
    _default_config_file='/etc/zabbix/zabbix_agentd.conf'

    def __init__(self, config_file=None, logger=None):
        if config_file is None:
            config_file=self._default_config_file

        if logger: # pragma: no cover
            self._logger = logger

        if self._logger: # pragma: no cover
            self._logger.info(
                "Initializing"
            )

        # Set default config value from sample zabbix_agentd.conf
        # Only exception is hostname. While non mandatory, we must have
        # This property set. Default goes to server FQDN
        # We do *NOT* support HostnameItem except to fake system.hostname
        self.config = {
            # Protobix specific options
            'data_type': None,
            'dryrun': False,
            # Zabbix Agent options
            'ServerActive': '127.0.0.1',
            'ServerPort': 10051,
            'LogType': 'file',
            'LogFile': '/tmp/zabbix_agentd.log',
            'DebugLevel': 3,
            'Timeout': 3,
            'Hostname': socket.getfqdn(),
            'TLSConnect': 'unencrypted',
            'TLSCAFile': None,
            'TLSCertFile': None,
            'TLSCRLFile': None,
            'TLSKeyFile': None,
            'TLSServerCertIssuer': None,
            'TLSServerCertSubject': None,
            'TLSPSKIdentity': None,
            'TLSPSKFile': None,
        }

        # list_values=False argument below is needed because of potential
        # UserParameter with spaces which breaks ConfigObj
        # See
        if self._logger: # pragma: no cover
            self._logger.debug(
                "Reading Zabbix Agent configuration file %s" %
                config_file
            )
        tmp_config = configobj.ConfigObj(config_file, list_values=False)

        # If not config_file found or provided,
        # we should fallback to the default
        if tmp_config == {}:
            if self._logger: # pragma: no cover
                self._logger.warn(
                    "Not configuration found"
                )
            return

        if self._logger: # pragma: no cover
            self._logger.debug(
                "Setting configuration"
            )
        if 'DebugLevel' in tmp_config:
            self.debug_level = int(tmp_config['DebugLevel'])

        if 'Timeout' in tmp_config:
            self.timeout = int(tmp_config['Timeout'])

        if 'Hostname' in tmp_config:
            self.hostname = tmp_config['Hostname']

        # Process LogType & LogFile & ServerACtive in separate methods
        # Due to custom logic
        self._process_server_config(tmp_config)
        self._process_log_config(tmp_config)
        self._process_tls_config(tmp_config)

    def _process_server_config(self, tmp_config):
        if self._logger: # pragma: no cover
            self._logger.debug(
                "Processing server config"
            )
        if 'ServerActive' in tmp_config:
            # Because of list_values=False above,
            # we have to check ServerActive format
            # and extract server & port manually
            # See  https://github.com/jbfavre/python-protobix/issues/16
            tmp_server = tmp_config['ServerActive'].split(',')[0] \
                if "," in tmp_config['ServerActive'] else tmp_config['ServerActive']
            self.server_active, server_port = \
                tmp_server.split(':') if ":" in tmp_server else (tmp_server, 10051)
            self.server_port = int(server_port)

    def _process_log_config(self, tmp_config):
        if self._logger: # pragma: no cover
            self._logger.debug(
                "Processing log config"
            )
        if 'LogType' in tmp_config and tmp_config['LogType'] in ['file', 'system', 'console']:
            self.log_type = tmp_config['LogType']
        elif 'LogType' in tmp_config:
            raise ValueError('LogType must be one of [file,system,console]')

        # At this point, LogType is one of [file,system,console]
        if  self.log_type in ['system', 'console']:
            # If LogType if console or system, we don't need LogFile
            self.log_file = None
        elif self.log_type == 'file':
            # LogFile will be used
            if 'LogFile' in tmp_config and tmp_config['LogFile'] == '-':
                # Zabbix 2.4 compatibility
                # LogFile to '-' means we want to use syslog
                self.log_file = None
                self.log_type = 'system'
            elif 'LogFile' in tmp_config:
                self.log_file = tmp_config['LogFile']

    def _process_tls_config(self, tmp_config):
        if self._logger: # pragma: no cover
            self._logger.debug(
                "Processing tls config"
            )
        if 'TLSConnect' in tmp_config:
            self.tls_connect = tmp_config['TLSConnect']

        if self.tls_connect == 'cert':
            if 'TLSCertFile' in tmp_config and \
               'TLSKeyFile' in tmp_config and \
               'TLSCAFile' in tmp_config:
                    self.tls_cert_file = tmp_config['TLSCertFile']
                    self.tls_key_file = tmp_config['TLSKeyFile']
                    self.tls_ca_file = tmp_config['TLSCAFile']
            else:
                raise ValueError('TLSConnect is cert. TLSCertFile, TLSKeyFile and TLSCAFile are mandatory')
            if 'TLSCRLFile' in tmp_config:
                self.tls_crl_file = tmp_config['TLSCRLFile']
            if 'TLSServerCertIssuer' in tmp_config:
                self.tls_server_cert_issuer = tmp_config['TLSServerCertIssuer']
            if 'TLSServerCertSubject' in tmp_config:
                self.tls_server_cert_subject = tmp_config['TLSServerCertSubject']

        if self.tls_connect == 'psk':
            if 'TLSPSKIdentity' in tmp_config and 'TLSPSKFile' in tmp_config:
                self.tls_psk_identity = tmp_config['TLSPSKIdentity']
                self.tls_psk_file = tmp_config['TLSPSKFile']
            else:
                raise ValueError('TLSConnect is psk. TLSPSKIdentity and TLSPSKFile are mandatory')

    @property
    def server_active(self):
        return self.config['ServerActive']

    @server_active.setter
    def server_active(self, value):
        if value:
            self.config['ServerActive'] = value

    @property
    def server_port(self):
        return self.config['ServerPort']

    @server_port.setter
    def server_port(self, value):
        # Must between 1024-32767 like ListenPort for Server & Proxy
        # https://www.zabbix.com/documentation/3.0/manual/appendix/config/zabbix_server
        if isinstance(value, int) and value >= 1024 and value <= 32767:
            self.config['ServerPort'] = value
        else:
            raise ValueError('ServerPort must be between 1024 and 32767')

    @property
    def log_type(self):
        if 'LogType' in self.config:
            return self.config['LogType']

    @log_type.setter
    def log_type(self, value):
        if value and value in ['file', 'system', 'console']:
            self.config['LogType'] = value

    @property
    def log_file(self):
        return self.config['LogFile']

    @log_file.setter
    def log_file(self, value):
        self.config['LogFile'] = value

    @property
    def debug_level(self):
        return self.config['DebugLevel']

    @debug_level.setter
    def debug_level(self, value):
        # Must be between 0 and 5
        # https://www.zabbix.com/documentation/3.0/manual/appendix/config/zabbix_agentd
        if isinstance(value, int) and value >= 0 and value <= 5:
            self.config['DebugLevel'] = value
        else:
            raise ValueError('DebugLevel must be between 0 and 5, ' + str(value) + ' provided')

    @property
    def timeout(self):
        return self.config['Timeout']

    @timeout.setter
    def timeout(self, value):
        # Must be between 1 and 30
        # https://www.zabbix.com/documentation/3.0/manual/appendix/config/zabbix_agentd
        if isinstance(value, int) and value > 0 and value <= 30:
            self.config['Timeout'] = value
        else:
            raise ValueError('Timeout must be between 1 and 30')

    @property
    def hostname(self):
        return self.config['Hostname']

    @hostname.setter
    def hostname(self, value):
        if value:
            self.config['Hostname'] = value

    @property
    def tls_connect(self):
        return self.config['TLSConnect']

    @tls_connect.setter
    def tls_connect(self, value):
        if value in ['unencrypted', 'psk', 'cert']:
            self.config['TLSConnect'] = value
        else:
            raise ValueError('TLSConnect must be one of [unencrypted,psk,cert]')

    @property
    def tls_ca_file(self):
        return self.config['TLSCAFile']

    @tls_ca_file.setter
    def tls_ca_file(self, value):
        if value:
            self.config['TLSCAFile'] = value

    @property
    def tls_cert_file(self):
        return self.config['TLSCertFile']

    @tls_cert_file.setter
    def tls_cert_file(self, value):
        if value:
            self.config['TLSCertFile'] = value

    @property
    def tls_crl_file(self):
        return self.config['TLSCRLFile']

    @tls_crl_file.setter
    def tls_crl_file(self, value):
        if value:
            self.config['TLSCRLFile'] = value

    @property
    def tls_key_file(self):
        return self.config['TLSKeyFile']

    @tls_key_file.setter
    def tls_key_file(self, value):
        if value:
            self.config['TLSKeyFile'] = value

    @property
    def tls_server_cert_issuer(self):
        return self.config['TLSServerCertIssuer']

    @tls_server_cert_issuer.setter
    def tls_server_cert_issuer(self, value):
        if value:
            self.config['TLSServerCertIssuer'] = value

    @property
    def tls_server_cert_subject(self):
        return self.config['TLSServerCertSubject']

    @tls_server_cert_subject.setter
    def tls_server_cert_subject(self, value):
        if value:
            self.config['TLSServerCertSubject'] = value

    @property
    def tls_psk_identity(self):
        return self.config['TLSPSKIdentity']

    @tls_psk_identity.setter
    def tls_psk_identity(self, value):
        if value:
            self.config['TLSPSKIdentity'] = value

    @property
    def tls_psk_file(self):
        return self.config['TLSPSKFile']

    @tls_psk_file.setter
    def tls_psk_file(self, value):
        if value:
            self.config['TLSPSKFile'] = value

    @property
    def dryrun(self):
        return self.config['dryrun']

    @dryrun.setter
    def dryrun(self, value):
        if value in [True, False]:
            self.config['dryrun'] = value
        else:
            raise ValueError('dryrun parameter requires boolean')

    @property
    def data_type(self):
        return self.config['data_type']

    @data_type.setter
    def data_type(self, value):
        if value in ['lld', 'items', None]:
            self.config['data_type'] = value
        else:
            raise ValueError('data_type requires either "items" or "lld"')
