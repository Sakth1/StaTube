import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import json


class DatabaseManager:
    def __init__(self, base_dir: Optional[str] = None, db_name: str = "data.db"):
        # Default location: ~/Documents/YTAnalysis/
        self.base_dir = Path(base_dir or Path.home() / "Documents" / "YTAnalysis")
        self.db_dir = self.base_dir / "DB"
        self.channel_dir = self.base_dir / "Channels"
        self.transcript_dir = self.base_dir / "Transcripts"
        self.comment_dir = self.base_dir / "Comments"
        self.proxy_dir = self.base_dir / "Proxies"
        self.video_dir = self.base_dir / "Videos"

        # Ensure directories exist
        for folder in [self.db_dir, self.transcript_dir, self.comment_dir, self.proxy_dir, self.video_dir]:
            folder.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {folder}")

        # Database connection
        self.db_path = self.db_dir / db_name
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()

        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS CHANNEL (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            handle TEXT,
            sub_count INTEGER,
            desc TEXT,
            created_at DATETIME,
            updated_at DATETIME
        );

        CREATE TABLE IF NOT EXISTS VIDEO (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER,
            title TEXT,
            desc TEXT,
            duration INTEGER,
            view_count INTEGER,
            like_count INTEGER,
            pub_date DATETIME,
            status TEXT,
            created_at DATETIME,
            file_path TEXT,
            FOREIGN KEY(channel_id) REFERENCES CHANNEL(id)
        );

        CREATE TABLE IF NOT EXISTS TRANSCRIPT (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            file_path TEXT,  -- reference to transcript file
            language TEXT,
            confidence REAL,
            created_at DATETIME,
            FOREIGN KEY(video_id) REFERENCES VIDEO(id)
        );

        CREATE TABLE IF NOT EXISTS COMMENT (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            author TEXT,
            file_path TEXT,  -- reference to comment file
            like_count INTEGER,
            pub_date DATETIME,
            created_at DATETIME,
            FOREIGN KEY(video_id) REFERENCES VIDEO(id)
        );

        CREATE TABLE IF NOT EXISTS PROXY (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT,
            port INTEGER,
            status TEXT,
            location TEXT,
            last_used DATETIME,
            created_at DATETIME,
            file_path TEXT -- reference to proxy log file
        );

        CREATE TABLE IF NOT EXISTS PROXY_USAGE (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proxy_id INTEGER,
            channel_id INTEGER,
            used_at DATETIME,
            operation TEXT,
            FOREIGN KEY(proxy_id) REFERENCES PROXY(id),
            FOREIGN KEY(channel_id) REFERENCES CHANNEL(id)
        );
        """)
        self.conn.commit()

    # ---------- Core Helpers ----------
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        keys = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = tuple(data.values())
        query = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        cursor = self.conn.cursor()
        cursor.execute(query, values)
        self.conn.commit()
        return cursor.lastrowid

    def fetch(self, table: str, where: Optional[str] = None, params: Tuple = ()) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM {table}"
        if where:
            query += f" WHERE {where}"
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def update(self, table: str, data: Dict[str, Any], where: str, params: Tuple) -> int:
        set_clause = ", ".join([f"{k}=?" for k in data.keys()])
        values = tuple(data.values()) + params
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        cursor = self.conn.cursor()
        cursor.execute(query, values)
        self.conn.commit()
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
        self.conn.close()
