from PySide6.QtCore import QObject, Signal

class AppState(QObject):
    channel_name_changed = Signal(str)
    channel_id_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._channel_name = None
        self._channel_id = None

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

# Global singleton instance
app_state = AppState()