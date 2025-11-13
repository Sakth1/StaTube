from PySide6.QtCore import QObject, Signal
from typing import Optional, Any

from Data.DatabaseManager import DatabaseManager


class AppState(QObject):
    """
    Global application state singleton.
    Stores shared data and proxy instance.
    """
    channel_info_changed = Signal(dict)
    video_list_changed = Signal(dict)
    video_list_appended = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self._channel_info = None
        self._video_list = None
        self._db = None


    @property
    def channel_info(self):
        return self._channel_info
    
    @channel_info.setter
    def channel_info(self, value: Any) -> dict:
        if value is None:
            return

        if isinstance(value, dict):
            self._channel_info = value
            self.channel_info_changed.emit(self._channel_info)

        elif isinstance(value, tuple) and len(value) == 2:
            key, value = value
            if self._channel_info[key] != value:
                self._channel_info[key] = value
                self.channel_info_changed.emit(self._channel_info)


    @property
    def video_list(self) -> dict:
        return self._video_list
    
    @video_list.setter
    def video_list(self, value: Any):
        if value is None:
            return
        
        if isinstance(value, dict):
            self._video_list = value
            self.video_list_changed.emit(self._video_list)

        if isinstance(value, tuple) and len(value) == 2:
            key, value = value
            if self._video_list[key] != value:
                self._video_list[key] = value
                self.video_list_appended.emit(self._video_list)

    
    @property
    def db(self) -> DatabaseManager:
        return self._db
    
    @db.setter
    def db(self, value: DatabaseManager):
        self._db = value


# Global singleton instance
app_state = AppState()