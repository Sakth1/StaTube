import scrapetube
from pathlib import Path
from datetime import datetime

from Data.DatabaseManager import DatabaseManager
from utils.Proxy import Proxy


class Search:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.channels = {}

    def search_channel(self, name: str = None):
        if not name:
            return {"None": {"title": None, "url": None}}
        
        proxy = Proxy().get_proxy()
        if proxy:
            pass
        else:
            proxy = None        

        self.channels = {}
        search_results = scrapetube.get_search(name, results_type="channel", limit=6)

        for ch in search_results:
            title = ch.get("title", {}).get("simpleText")
            sub_count = ch.get("videoCountText", {}).get("simpleText")
            channel_id = ch.get("channelId")

            if channel_id:
                url = f"https://www.youtube.com/channel/{channel_id}"
                self.channels[channel_id] = {"title": title, "url": url, "sub_count": sub_count}

                # ---- Save JSON to file ----
                file_path = self.db.save_json_file(
                    self.db.base_dir / "Channels",
                    f"channel_{channel_id}",
                    {"id": channel_id, "title": title, "url": url},
                )

                # ---- Store reference in DB ----
                self.db.insert(
                    "CHANNEL",
                    {
                        "name": title,
                        "handle": channel_id,  # if no @handle, we use channelId
                        "sub_count": 0,  # not available here
                        "desc": None,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                    },
                )

        return self.channels

