import scrapetube
from pathlib import Path
from datetime import datetime
from Data.DatabaseManager import DatabaseManager


class Search:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.channels = {}

    def search_channel(self, name: str = None):
        if not name:
            return {"None": {"title": None, "url": None}}

        self.channels = {}
        search_results = scrapetube.get_search(name, results_type="channel", limit=6)

        for ch in search_results:
            title = ch.get("title", {}).get("simpleText")
            channel_id = ch.get("channelId")

            if channel_id:
                url = f"https://www.youtube.com/channel/{channel_id}"
                self.channels[channel_id] = {"title": title, "url": url}

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

if __name__ == "__main__":
    db = DatabaseManager()
    search = Search(db)

    results = search.search_channel("mrbeast")

    for cid, data in results.items():
        print(f"Title: {data['title']} | URL: {data['url']}")

    # Fetch from DB later
    rows = db.fetch("CHANNEL", "handle=?", (cid,))
    print("DB Row:", rows)

    # Load JSON file reference
    file_path = db.base_dir / "Channels" / f"channel_{cid}.json"
    print("File contents:", db.load_json_file(file_path))

    db.close()
