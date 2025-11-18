from PySide6.QtCore import QObject, Signal
from typing import Optional, Any, Dict, List

from Data.DatabaseManager import DatabaseManager


class AppState(QObject):
    """
    Global application state singleton.
    
    Stores shared data and proxy instance.
    
    Attributes:
        channel_info (dict): Stores channel information such as channel ID, name, and profile picture.
        video_list (dict): Stores video information such as video ID, title, and channel ID.
        db (DatabaseManager): Stores database instance.
    
    Signals:
        channel_info_changed (dict): Emitted when channel information changes.
        video_list_changed (dict): Emitted when video list changes.
        video_list_appended (dict): Emitted when video list is appended.
    """
    channel_info_changed = Signal(dict)
    video_list_changed = Signal(dict)
    video_list_appended = Signal(dict)
    
    def __init__(self, channel_info: Optional[dict] = None, video_list: Optional[dict] = None, db: Optional[DatabaseManager] = None) -> None:
        """
        Initializes the AppState instance.

        Args:
            channel_info (Optional[dict]): Stores channel information such as channel ID, name, and profile picture.
            video_list (Optional[dict]): Stores video information such as video ID, title, and channel ID.
            db (Optional[DatabaseManager]): Stores database instance.
        """
        super().__init__()
        self._channel_info: Optional[dict] = channel_info
        self._video_list: Optional[dict] = video_list
        self._db: Optional[DatabaseManager] = db

    @property
    def channel_info(self) -> Optional[Dict[str, Any]]:
        """
        Stores channel information such as channel ID, name, and profile picture.

        Returns:
            Optional[Dict[str, Any]]: Channel information or None if not set.
        """
        return self._channel_info
    
    @channel_info.setter
    def channel_info(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sets channel information and emits channel_info_changed signal.
        
        Args:
            value (Dict[str, Any]): New channel information to set.
        
        Returns:
            Dict[str, Any]: New channel information.
        """
        if value is None:
            return self._channel_info

        if isinstance(value, dict):
            self._channel_info = value
            self.channel_info_changed.emit(self._channel_info)

        elif isinstance(value, tuple) and len(value) == 2:
            key, value = value
            if self._channel_info.get(key) != value:
                self._channel_info[key] = value
                self.channel_info_changed.emit(self._channel_info)

    @property
    def video_list(self) -> Dict[str, List[str]]:
        """
        Stores video information such as video ID, title, and channel ID.

        Returns:
            Dict[str, List[str]]: Video information with channel ID as key and list of video IDs as value.
        """
        return self._video_list
    
    @video_list.setter
    def video_list(self, value: Dict[str, List[str]]) -> None:
        """
        Sets video list and emits video_list_changed signal.

        Args:
            value (Dict[str, List[str]]): New video list to set.
        """
        if value is None:
            return
        
        if isinstance(value, dict):
            self._video_list = value
            self.video_list_changed.emit(self._video_list)

        if isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str) and isinstance(value[1], list):
            key, value = value
            if self._video_list.get(key) != value:
                self._video_list[key] = value
                self.video_list_appended.emit(self._video_list)

    
    @property
    def db(self) -> DatabaseManager:
        """
        Stores database instance.
        
        Returns:
            DatabaseManager: Database instance.
        """
        return self._db
    
    @property
    def db(self) -> DatabaseManager:
        """
        Gets the database instance.

        Returns:
            DatabaseManager: The database instance.
        """
        return self._db
    
    @db.setter
    def db(self, value: DatabaseManager) -> None:
        """
        Sets the database instance.

        Args:
            value (DatabaseManager): The new database instance to set.
        """
        self._db = value

# Global singleton instance
app_state = AppState()