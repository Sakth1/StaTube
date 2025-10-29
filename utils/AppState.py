from PySide6.QtCore import QObject, Signal

from Data.DatabaseManager import DatabaseManager
from .Proxy import Proxy

class ProxyThread():
    def __init__(self):
        self.proxy = Proxy()
    
    def start(self):
        self.proxy_thread = threading.Thread(target=self.update_proxy, daemon=True)
        self.proxy_thread.start()
    
    def update_proxy(self):
        while True:
            self.proxy_url = self.proxy.get_working_proxy()
            time.sleep(100)

class AppState(QObject):
    channel_name_changed = Signal(str)
    channel_id_changed = Signal(str)
    channel_url_changed = Signal(str)

    db = DatabaseManager()

    def __init__(self):
        super().__init__()
        self._channel_name = None
        self._channel_id = None
        self._channel_url = None

    @property
    def channel_name(self):
        return self._channel_name

    @channel_name.setter
    def channel_name(self, value):
        self._channel_name = value
        self.channel_name_changed.emit(value)

    @property
    def channel_id(self):
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value):
        self._channel_id = value
        self.channel_id_changed.emit(value)

    @property
    def channel_url(self):
        return self._channel_url

    @channel_url.setter
    def channel_url(self, value):
        self._channel_url = value  # fixed line
        self.channel_url_changed.emit(value)

# Global singleton instance
app_state = AppState()
