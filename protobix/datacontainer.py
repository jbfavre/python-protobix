import simplejson
import time

from .senderprotocol import SenderProtocol

class DataContainer(SenderProtocol):

    REQUEST = "sender data"
    _data_type = None
    _items_list = []

    def __init__(self, zbx_host  = '127.0.0.1',
                       zbx_port  = 10051,
                       debug     = False,
                       dryrun    = False,
                       data_type = None):
        super( DataContainer, self).__init__(zbx_host  = zbx_host,
                                             zbx_port  = zbx_port,
                                             debug     = debug,
                                             dryrun    = dryrun)

    @property
    def data_type(self):
        return self._data_type

    @data_type.setter
    def data_type(self, value):
        if value in ['lld', 'items']:
          self._data_type = value
          # Clean _items_list & _result when changing _data_type
          # Incompatible format
          self._items_list = []
          self._result = []
        else:
            raise ValueError('Only support either "items" or "lld"')

    @property
    def items_list(self):
        return self._items_list

    @property
    def clock(self):
        return int((time.time())/60*60)

    def add_item(self, host, key, value, clock=None):
        if clock is None:
            clock = self.clock
        if self._data_type == "items":
            item = { "host": host, "key": key,
                     "value": value, "clock": clock}
        elif self._data_type == "lld":
            item = { "host": host, "key": key, "clock": clock,
                     "value": simplejson.dumps({"data":value}) }
        else:
            raise ValueError('Setup data_type before adding data')
        self._items_list.append(item)

    def add(self, data):
        for host in data:
            for key in data[host]:
                if not data[host][key] == []:
                    self.add_item( host, key, data[host][key])