import yt_dlp
import webvtt
import os
import json
from pathlib import Path
from utils.Proxy import Proxy
from Data.DatabaseManager import DatabaseManager  # new DB reference


class Transcription:
    def __init__(self, db: DatabaseManager, base_dir=None):
        """
        Handles downloading, parsing, and saving YouTube video transcripts.
        Stores transcript files under ~/Documents/YTAnalysis/Transcripts/
        and saves references in the SQLite DB.
        """
        self.db = db

        self.base_dir = self.db.base_dir
        self.transcripts_dir = self.base_dir / "Transcripts"
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)

    def get_transcripts(self, urls: list[str], channel_id: str, lang: str = "en") -> dict:
        """
        Downloads transcripts for a list of YouTube video URLs,
        saves them into JSON files under Transcripts/,
        and inserts file references into the database.
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

        proxy = Proxy().get_proxy()
        if proxy:
            ydl_opts["proxy"] = proxy
            print(f"[INFO] Using proxy for transcriptions: {proxy}")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                for url in urls:
                    try:
                        info_dict = ydl.extract_info(url, download=True)
                        video_id = info_dict.get("id")
                        title = info_dict.get("title", "Unknown Title")

                        # Find VTT file in working dir
                        vtt_filename = next(
                            (f for f in os.listdir() if f.endswith(".vtt") and video_id in f),
                            None
                        )
                        if not vtt_filename:
                            print(f"[WARN] No VTT subtitle found for {url}")
                            continue

                        # Parse transcript
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

                        # Save per-video transcript JSON
                        video_file = self.transcripts_dir / f"{video_id}_transcript.json"
                        with open(video_file, "w", encoding="utf-8") as vf:
                            json.dump(video_transcript, vf, indent=2, ensure_ascii=False)

                        # Insert reference in DB
                        self.db.insert_transcript_reference(
                            channel_id=channel_id,
                            video_id=video_id,
                            transcript_path=str(video_file)
                        )

                        # Clean up .vtt
                        os.remove(vtt_filename)

                        print(f"[INFO] Transcript saved: {video_file}")

                    except Exception as ve:
                        print(f"[ERROR] Failed to fetch transcript for {url}: {ve}")

            # Save combined transcripts (optional)
            combined_file = self.transcripts_dir / f"{channel_id}_all_transcripts.json"
            with open(combined_file, "w", encoding="utf-8") as f:
                json.dump(all_transcripts, f, indent=2, ensure_ascii=False)

            print(f"[INFO] All transcripts saved to: {combined_file}")
            return all_transcripts

        except Exception as e:
            print(f"[ERROR] Transcription process failed: {e}")
            return {}
