import scrapetube
from pathlib import Path
from datetime import datetime
import urllib.request

from Data.DatabaseManager import DatabaseManager
from utils.Proxy import Proxy


class Search:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.channels = {}

    def search_channel(self, name: str = None, limit: int = 6):
        if not name:
            return {"None": {"title": None, "url": None}}
        
        proxy = Proxy().get_proxy()
        if proxy:
            pass
        else:
            proxy = None

        self.channels = {}
        search_results = scrapetube.get_search(name, results_type="channel", limit=limit)

        for ch in search_results:
            title = ch.get("title", {}).get("simpleText")
            sub_count = ch.get("videoCountText", {}).get("accessibility", {}).get("accessibilityData", {}).get("label")
            desc = ch.get("descriptionSnippet", {}).get("runs")[0].get("text") if ch.get("descriptionSnippet") else None
            channel_id = ch.get("channelId")
            profile_url = "https:" + ch.get("thumbnail", {}).get("thumbnails")[0].get("url")
            
            try:
                urllib.request.urlretrieve(profile_url, rf"{self.db.profile_pic_dir}/{channel_id}.jpg")
                print(f'pic saved to {self.db.profile_pic_dir}/{channel_id}.jpg')
            except Exception as e:
                print(f"Failed to save profile picture: {e}")

            if channel_id:
                url = f"https://www.youtube.com/channel/{channel_id}"
                self.channels[channel_id] = {"title": title, "url": url, "sub_count": sub_count}

                # Check if channel already exists
                existing_channels = self.db.fetch("CHANNEL", where="channel_id = ?", params=(channel_id,))
                
                if not existing_channels:
                    # Channel doesn't exist, insert new one
                    self.db.insert(
                        "CHANNEL",
                        {
                            "channel_id": channel_id,
                            "name": title,
                            "url": url,
                            "sub_count": str(sub_count),
                            "desc": desc,
                            "profile_pic": f"{channel_id}.jpg",
                        },
                    )
                    print(f"Added new channel: {title}")

        return self.channels

