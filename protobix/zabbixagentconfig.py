import configobj
import socket

class ZabbixAgentConfig(object):

    def __init__(self, config_file='/etc/zabbix/zabbix_agentd.conf'):

        # Set default config value from sample zabbix_agentd.conf
        # Only exception is hostname. While non mandatory, we must have
        # This property set. Default goes to server FQDN
        # We do *NOT* support HostnameItem except to fake system.hostname
        self.config = {
            'ServerActive': '127.0.0.1',
            'ServerPort': 10051,
            'LogType': 'file',
            'LogFile': '/tmp/zabbix_agentd.log',
            'DebugLevel': 3,
            'Timeout': 3,
            'Hostname': socket.getfqdn()
        }

        # list_values=False argument bellow is needed because of potential
        # UserParameter with spaces which breaks ConfigObj
        # See 
        tmp_config = configobj.ConfigObj(config_file, list_values=False)

        # If not config_file found or provided,
        # we should fallback to the default
        if tmp_config == {}:
            return

        if 'DebugLevel' in tmp_config:
            self.debug_level = int(tmp_config['DebugLevel'])

        if 'Timeout' in tmp_config:
            self.timeout = int(tmp_config['Timeout'])

        if 'Hostname' in tmp_config:
            self.hostname = tmp_config['Hostname']

        # Process LogType & LogFile & ServerACtive in separate methods
        # Due to custom logic
        self._process_server_active(tmp_config)
        self._process_log_type(tmp_config)
        self._process_log_file(tmp_config)

    def _process_server_active(self, tmp_config):
        if 'ServerActive' in tmp_config:
            # Because of list_values=False above,
            # we have to check ServerActive format
            # and extract server & port manually
            tmp_server = tmp_config['ServerActive'].split(',')[0] \
                if "," in tmp_config['ServerActive'] else tmp_config['ServerActive']
            self.server_active, server_port = \
                tmp_server.split(':') if ":" in tmp_server else (tmp_server, 10051)
            self.server_port = int(server_port)

    def _process_log_type(self, tmp_config):
        if 'LogType' in tmp_config:
            if tmp_config['LogType'] in ['file', 'system', 'console']:
                self.log_type = tmp_config['LogType']
            else:
                raise ValueError('LogType must be one of [file,system,console]')
        else:
            self.log_type = 'file'

    def _process_log_file(self, tmp_config):
        if 'LogFile' in tmp_config and tmp_config['LogFile'] == '-':
            self.log_file = None
            self.log_type = 'system'
        elif 'LogFile' in tmp_config and tmp_config['LogFile'] != '-':
            if self.log_type == 'file':
                self.log_file = tmp_config['LogFile']
            else:
                self.log_file = None
        else:
            if self.log_type == 'file':
                raise ValueError('LogType set to file. LogFile is mandatory')
            else:
                self.log_file = None

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
        # https://www.zabbix.com/documentation/3.0/manual/appendix/config/zabbix_proxy
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
            raise ValueError('DebugLevel must be between 0 and 5')

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
