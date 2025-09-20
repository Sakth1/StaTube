import os
import json
from pathlib import Path

class CacheManager():
    def __init__(self, folder="Data"):
        self.folder = Path(folder)
        self.folder.mkdir(exist_ok=True)

    def _get_path(self, name: str) -> Path:
        return self.folder / f"{name}.json"

    def load(self, name: str) -> dict:
        path = self._get_path(name)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def save(self, name: str, data: dict):
        path = self._get_path(name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
