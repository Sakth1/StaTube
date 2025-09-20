import yt_dlp
import webvtt
import os
import json
from pathlib import Path

class Transcription:
    def __init__(self, data_folder="Data"):
        self.data_folder = Path(data_folder)
        self.data_folder.mkdir(exist_ok=True)

    def get_transcripts(self, urls: list[str], channel_id: str, lang: str = "en") -> dict:
        """
        Downloads transcripts for a list of YouTube video URLs,
        stores them in a single JSON file under Data/<channel_id>_transcripts.json,
        and returns the transcript dict.
        """
        all_transcripts = {
            "channel_id": channel_id,
            "language": lang,
            "videos": []
        }

        ydl_opts = {
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitlesformat": "vtt",
            "subtitleslangs": [lang],
            "skip_download": True,
            "outtmpl": "%(id)s.%(ext)s",
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                for url in urls:
                    try:
                        info_dict = ydl.extract_info(url, download=True)
                        video_id = info_dict.get("id")
                        title = info_dict.get("title", "Unknown Title")

                        # ✅ Find VTT file
                        vtt_filename = None
                        for file in os.listdir():
                            if file.endswith(".vtt") and video_id in file:
                                vtt_filename = file
                                break
                        if not vtt_filename:
                            print(f"⚠️ No VTT subtitle found for {url}")
                            continue

                        # ✅ Parse transcript
                        video_transcript = {
                            "video_id": video_id,
                            "title": title,
                            "url": url,
                            "captions": []
                        }

                        for caption in webvtt.read(vtt_filename):
                            video_transcript["captions"].append({
                                "start": caption.start,
                                "end": caption.end,
                                "text": caption.text
                            })

                        all_transcripts["videos"].append(video_transcript)

                        # ✅ Clean up .vtt
                        os.remove(vtt_filename)

                        print(f"✅ Transcript processed: {title} ({video_id})")

                    except Exception as ve:
                        import traceback
                        traceback.print_exc()
                        print(f"❌ Failed to fetch transcript for {url}: {ve}")

            # ✅ Save all transcripts in one file
            output_file = self.data_folder / f"{channel_id}_transcripts.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_transcripts, f, indent=2, ensure_ascii=False)

            print(f"📂 All transcripts saved to: {output_file}")
            return all_transcripts

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Error while processing transcripts: {e}")
            return {}
