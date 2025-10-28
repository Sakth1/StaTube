import scrapetube
import httpx

from Data.DatabaseManager import DatabaseManager
from utils.Proxy import Proxy


async def download_with_proxy(url, save_path, proxy_url=Proxy().get_working_proxy()):
    async with httpx.AsyncClient(proxies=proxy_url, timeout=15.0) as client:
        async with client.stream("GET", url) as r:
            r.raise_for_status()
            with open(save_path, "wb") as f:
                async for chunk in r.aiter_bytes():
                    f.write(chunk)

class Search:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.channels = {}

    def search_channel(self, name: str = None, limit: int = 6):
        if not name:
            return {"None": {"title": None, "url": None}}

        self.channels = {}
        search_results = scrapetube.get_search(name, results_type="channel", limit=limit)
        proxy_url = Proxy().get_working_proxy()

        for ch in search_results:
            title = ch.get("title", {}).get("simpleText")
            sub_count = ch.get("videoCountText", {}).get("accessibility", {}).get("accessibilityData", {}).get("label")
            desc = ch.get("descriptionSnippet", {}).get("runs")[0].get("text") if ch.get("descriptionSnippet") else None
            channel_id = ch.get("channelId")
            profile_url = "https:" + ch.get("thumbnail", {}).get("thumbnails")[0].get("url")
                        
            try:
                profile_save_path = rf"{self.db.profile_pic_dir}/{channel_id}.png"
                download_with_proxy(profile_url, profile_save_path, proxy_url)
            except Exception as e:
                print(f"Failed to save profile picture: {e}")
                import traceback
                traceback.print_exc()

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

