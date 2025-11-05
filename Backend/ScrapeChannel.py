import scrapetube
import requests
import threading

from utils.AppState import app_state

def download_img(url, save_path):
    try:
        response = requests.get(url, timeout=15.0, stream=True) #TODO: add proxies here in future 
        response.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        print(f"[ERROR] Failed to download {url}: {e}")

class Search:
    def __init__(self):
        self.db = app_state.db
        self.channels = {}

    def update_db(self, channel_id, title, sub_count, desc, profile_url):
        try:
            profile_save_path = rf"{self.db.profile_pic_dir}/{channel_id}.png"
            download_img(profile_url, profile_save_path)
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

    def search_channel(self, name: str = None, limit: int = 6, stop_event=None, final=False):
        if not name:
            return {"None": {"title": None, "url": None}}

        self.channels = {}
        search_results = scrapetube.get_search(name, results_type="channel", limit=limit)

        for ch in search_results:
            # Check if we should stop
            if stop_event and stop_event.is_set():
                print("Search interrupted")
                return self.channels
            
            title = ch.get("title", {}).get("simpleText")
            sub_count = ch.get("videoCountText", {}).get("accessibility", {}).get("accessibilityData", {}).get("label")
            desc = ch.get("descriptionSnippet", {}).get("runs")[0].get("text") if ch.get("descriptionSnippet") else None
            channel_id = ch.get("channelId")
            profile_url = "https:" + ch.get("thumbnail", {}).get("thumbnails")[0].get("url")

            if channel_id:
                url = f"https://www.youtube.com/channel/{channel_id}"
                self.channels[channel_id] = {"title": title, "url": url, "sub_count": sub_count}

            threading.Thread(target=self.update_db, args=(channel_id, title, sub_count, desc, profile_url), daemon=True).start()                            

        return self.channels