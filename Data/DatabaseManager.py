import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import json
import platform
import os
import threading

class DatabaseManager:
    def __init__(self, base_dir: Optional[str] = None, db_name: str = "data.db"):
        # Determine OS and set appropriate AppData directory
        system = platform.system()
        
        if system == "Windows":
            app_data_dir = Path(os.environ.get('APPDATA', Path.home() / "AppData" / "Roaming"))
        elif system == "Darwin":  # macOS
            app_data_dir = Path.home() / "Library" / "Application Support"
        else:  # Linux and other Unix-like systems
            app_data_dir = Path.home() / ".local" / "share"
        
        # Set base directory to AppData/YTAnalysis
        self.base_dir = Path(base_dir or app_data_dir / "YTAnalysis")
        self.db_dir = self.base_dir / "DB"
        self.channel_dir = self.base_dir / "Channels"
        self.profile_pic_dir = self.base_dir / "ProfilePics"
        self.transcript_dir = self.base_dir / "Transcripts"
        self.thumbnail_dir = self.base_dir / "Thumbnails"
        self.comment_dir = self.base_dir / "Comments"
        self.proxy_dir = self.base_dir / "Proxies"
        self.video_dir = self.base_dir / "Videos"

        # Ensure directories exist
        for folder in [self.db_dir, self.transcript_dir, self.comment_dir,
                       self.proxy_dir, self.video_dir, self.channel_dir,
                       self.profile_pic_dir, self.thumbnail_dir]:
            folder.mkdir(parents=True, exist_ok=True)

        # Thread-local storage for database connections
        self._local = threading.local()
        self.db_path = self.db_dir / db_name
        self._create_tables()

    def _get_connection(self):
        """Get thread-specific database connection"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _create_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS CHANNEL (
            channel_id TEXT PRIMARY KEY,
            name TEXT,
            url TEXT,
            sub_count TEXT,
            desc TEXT,
            profile_pic TEXT
        );

        CREATE TABLE IF NOT EXISTS VIDEO (
            video_id TEXT PRIMARY KEY,
            channel_id TEXT,
            video_type TEXT,
            video_url TEXT,
            title TEXT,
            desc TEXT,
            duration TEXT,
            view_count TEXT,
            like_count TEXT,
            pub_date DATETIME,
            status TEXT,
            FOREIGN KEY(channel_id) REFERENCES CHANNEL(channel_id)
        );

        CREATE TABLE IF NOT EXISTS TRANSCRIPT (
            transcript_id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT, 
            file_path TEXT,
            language TEXT,
            FOREIGN KEY(video_id) REFERENCES VIDEO(video_id)
        );

        CREATE TABLE IF NOT EXISTS COMMENT (
            comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            file_path TEXT,
            FOREIGN KEY(video_id) REFERENCES VIDEO(video_id)
        );
        """)
        conn.commit()

    # ---------- Core Helpers ----------
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        conn = self._get_connection()
        keys = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = tuple(data.values())
        query = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        cursor.execute(query, values)
        conn.commit()
        return cursor.lastrowid

    def fetch(self, table: str, where: Optional[str] = None, params: Tuple = ()) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        query = f"SELECT * FROM {table}"
        if where:
            query += f" WHERE {where}"
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def update(self, table: str, data: Dict[str, Any], where: str, params: Tuple) -> int:
        conn = self._get_connection()
        set_clause = ", ".join([f"{k}=?" for k in data.keys()])
        values = tuple(data.values()) + params
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount

    # ---------- File Management Helpers ----------
    def save_json_file(self, folder: Path, filename: str, data: Dict) -> Path:
        filepath = folder / f"{filename}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return filepath

    def load_json_file(self, filepath: Path) -> Dict:
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def close(self):
        """Close the thread-specific connection"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            del self._local.conn