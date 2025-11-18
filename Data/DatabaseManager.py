import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import json
import platform
import os
import threading

class DatabaseManager:
    def __init__(self, base_dir: Optional[str] = None, db_name: str = "data.db", schema_path: str = "schema.sql"):
        # Determine OS and set appropriate AppData directory
        system = platform.system()
        
        if system == "Windows":
            app_data_dir = Path(os.environ.get('APPDATA', Path.home() / "AppData" / "Roaming"))
        elif system == "Darwin":  # macOS
            app_data_dir = Path.home() / "Library" / "Application Support"
        else:  # Linux and others
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
        for folder in [
            self.db_dir, self.transcript_dir, self.comment_dir,
            self.proxy_dir, self.video_dir, self.channel_dir,
            self.profile_pic_dir, self.thumbnail_dir
        ]:
            folder.mkdir(parents=True, exist_ok=True)

        # Thread-local storage
        self._local = threading.local()
        self.db_path = self.db_dir / db_name

        # Load schema file
        cwd = os.path.dirname(os.path.abspath(__file__))
        self.schema_path = Path(os.path.join(cwd, schema_path))

        # Create tables using schema.sql
        self._create_tables()

    def _get_connection(self):
        """Get thread-specific database connection"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _create_tables(self):
        """Load schema.sql and execute it."""
        if not self.schema_path.exists():
            print(self.schema_path)
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        with open(self.schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()

    # ---------- Core Helpers ----------
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        conn = self._get_connection()
        keys = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        values = tuple(data.values())
        query = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, values)
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                if table == "VIDEO":
                    pk_column = "video_id"
                elif table == "CHANNEL":
                    pk_column = "channel_id"
                else:
                    raise

                if pk_column in data:
                    pk_value = data[pk_column]
                    update_data = {k: v for k, v in data.items() if k != pk_column}
                    return self.update(table, update_data, f"{pk_column}=?", (pk_value,))
                else:
                    raise
            else:
                raise

    def fetch(self, table: str, where: Optional[str] = None,
              order_by: Optional[str] = None, params: Tuple = ()) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        query = f"SELECT * FROM {table}"
        if where:
            query += f" WHERE {where}"
        if order_by:
            query += f" ORDER BY {order_by}"

        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def update(self, table: str, data: Dict[str, Any], where: str, params: Tuple) -> int:
        conn = self._get_connection()
        set_clause = ", ".join([f"{k}=?" for k in data.keys()])
        values = tuple(data.values()) + params
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        return cursor.rowcount

    # ---------- File Helpers ----------
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
        if hasattr(self._local, 'conn'):
            self._local.conn.close()
            del self._local.conn
