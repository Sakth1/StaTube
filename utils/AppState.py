from PySide6.QtCore import QObject, Signal

class AppState(QObject):
    """
    Global application state singleton.
    Stores shared data and proxy instance.
    """
    channel_name_changed = Signal(str)
    channel_id_changed = Signal(str)
    channel_url_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._channel_name = None
        self._channel_id = None
        self._channel_url = None
        self._db = None
        self._proxy = None  # Shared proxy instance
        
    @property
    def channel_name(self):
        return self._channel_name
    
    @channel_name.setter
    def channel_name(self, value):
        if self._channel_name != value:
            self._channel_name = value
            self.channel_name_changed.emit(value)
    
    @property
    def channel_id(self):
        return self._channel_id
    
    @channel_id.setter
    def channel_id(self, value):
        if self._channel_id != value:
            self._channel_id = value
            self.channel_id_changed.emit(value)
    
    @property
    def channel_url(self):
        return self._channel_url
    
    @channel_url.setter
    def channel_url(self, value):
        if self._channel_url != value:
            self._channel_url = value
            self.channel_url_changed.emit(value)
    
    @property
    def db(self):
        return self._db
    
    @db.setter
    def db(self, value):
        self._db = value
    
    @property
    def proxy(self):
        """Get the shared Proxy instance"""
        return self._proxy
    
    @proxy.setter
    def proxy(self, value):
        """Set the shared Proxy instance (should only be called once at startup)"""
        if self._proxy is None:
            self._proxy = value
        else:
            print("[WARN] Attempted to override existing proxy instance!")

# Global singleton instance
app_state = AppState()