import scrapetube
import urllib.request

from Data.DatabaseManager import DatabaseManager
from utils.Proxy import Proxy

def download_with_proxy(profile_url, profile_save_path, proxy_url=None):
    if proxy_url:
        proxy_handler = urllib.request.ProxyHandler({
            'http': proxy_url,
            'https': proxy_url
        })
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)

    urllib.request.urlretrieve(profile_url, profile_save_path)

class Search:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.channels = {}

    def search_channel(self, name: str = None, limit: int = 6):
        if not name:
            return {"None": {"title": None, "url": None}}

        self.channels = {}
        search_results = scrapetube.get_search(name, results_type="channel", limit=limit)

        for ch in search_results:
            title = ch.get("title", {}).get("simpleText")
            sub_count = ch.get("videoCountText", {}).get("accessibility", {}).get("accessibilityData", {}).get("label")
            desc = ch.get("descriptionSnippet", {}).get("runs")[0].get("text") if ch.get("descriptionSnippet") else None
            channel_id = ch.get("channelId")
            profile_url = "https:" + ch.get("thumbnail", {}).get("thumbnails")[0].get("url")
            
            try:
                profile_save_path = rf"{self.db.profile_pic_dir}/{channel_id}.png"
                download_with_proxy(profile_url, profile_save_path, Proxy().get_working_proxy())
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
                            "profile_pic": profile_save_path,
                        },
                    )
                    print(f"Added new channel: {title}")

        return self.channels

