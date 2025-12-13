from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, FetchedTranscript, TranscriptsDisabled
from youtube_transcript_api.formatters import JSONFormatter
import os
from PySide6.QtCore import QObject, Signal

from Data.DatabaseManager import DatabaseManager
from utils.AppState import app_state
from utils.Logger import logger


class TranscriptWorker(QObject):
    """
    Worker thread for fetching transcripts to keep UI responsive.
    """
    progress_updated = Signal(str)
    progress_percentage = Signal(int)
    finished = Signal()

    def __init__(self, video_details: dict[str, list], languages: list = ["en"]) -> None:
        """
        Initializes the TranscriptWorker.

        Args:
            video_details (dict): Dictionary of channel IDs and video ID lists.
            languages (list): List of language codes.
        """
        super().__init__()
        self.video_details = video_details
        self.languages = languages
        self.fetcher = TranscriptFetcher()

    def run(self) -> None:
        """
        Executes the transcript fetching process.
        Shows human-friendly names (video title) in progress messages when available.
        """
        try:
            total_videos = sum(len(v_list) for v_list in self.video_details.values())
            processed_count = 0

            self.progress_updated.emit("Starting transcript scrape...")
            self.progress_percentage.emit(0)

            language_option = ["en"]

            # helper to get title from DB
            def _get_title(vid, ch):
                try:
                    rows = self.fetcher.db.fetch("VIDEO", where="video_id=?", params=(vid,))
                    if rows:
                        return rows[0].get("title") or vid
                except Exception:
                    pass
                return vid

            for channel_id, video_id_list in self.video_details.items():
                # try get channel name
                try:
                    ch_rows = self.fetcher.db.fetch("CHANNEL", where="channel_id=?", params=(channel_id,))
                    channel_name = ch_rows[0].get("channel_name") if ch_rows else str(channel_id)
                except Exception:
                    channel_name = str(channel_id)

                for video_id in video_id_list:
                    video_title = _get_title(video_id, channel_id)
                    self.progress_updated.emit(f"Fetching transcript for: \"{video_title}\"")
                    # Perform fetch
                    result = self.fetcher._fetch(video_id, channel_id, language_option)

                    processed_count += 1
                    percentage = int((processed_count / total_videos) * 100)
                    self.progress_percentage.emit(percentage)

                    if result.get("filepath"):
                        self.progress_updated.emit(f"Saved: \"{video_title}\"")
                    else:
                        self.progress_updated.emit(f"Skipped: \"{video_title}\" ({result.get('remarks')})")

            self.progress_updated.emit("Transcript scraping completed!")
            self.progress_percentage.emit(100)
            self.finished.emit()

        except Exception as e:
            logger.exception(f"Error: {str(e)}")
            self.progress_updated.emit(f"Error: {str(e)}")
            self.finished.emit()


class TranscriptFetcher:
    """
    A class to fetch YouTube video transcripts using youtube-transcript-api.

    Attributes:
        db (DatabaseManager): The database manager instance.
        video_transcripts (dict): A dictionary storing the fetched transcripts.
    """
    def __init__(self) -> None:
        """Initializes the TranscriptFetcher instance."""
        self.db: DatabaseManager = app_state.db
        self.video_transcripts: dict = {}

    def _fetch(self, video_id: str, channel_id: str, language_option: tuple = ("en",)) -> dict:
        """
        Fetches a YouTube video transcript using youtube-transcript-api.

        Args:
            video_id (str): The YouTube video ID.
            channel_id (str): The channel ID for organizing storage.
            language_option (tuple): A tuple of language codes to fetch the transcript.

        Returns:
            dict: A dictionary containing the fetched transcript data.
        """
        # Try to get a manual transcript first, fall back to generated
        try:
            transcript_list = YouTubeTranscriptApi().list(video_id=video_id)
            try:
                # First try to get manual English transcript
                transcript = transcript_list.find_manually_created_transcript(language_codes=["en"])
            except NoTranscriptFound:
                try:
                    # Then try generated English transcript
                    transcript = transcript_list.find_generated_transcript(language_codes=["en"])
                except NoTranscriptFound:
                    # Finally, try to get English translation from any available transcript
                    transcript = transcript_list.find_transcript(language_codes=["en"])
            
            transcript_data = transcript.fetch()
            filename = f"{video_id}.json"
            filepath = self.save_transcript(transcript_data, channel_id, filename)
            logger.info(f"Transcript saved for video_id={video_id}")
            
            # Structure the result
            result = {
                'video_id': video_id,
                'filepath': filepath,
                'language': transcript.language_code,
                'is_generated': transcript.is_generated,
                'remarks': None
            }
        
        except TranscriptsDisabled:
            logger.warning(f"Transcripts disabled for {video_id}")
            result = {
                'video_id': video_id,
                'filepath': None,
                'language': None,
                'is_generated': None,
                'remarks': "Transcripts disabled"
            }

        except Exception as e:
            logger.error(f"Error fetching transcript for {video_id}")
            logger.exception("Transcript fetch error:")
            result = {
                'video_id': video_id,
                'filepath': None,
                'language': None,
                'is_generated': None,
                'remarks': "Transcripts disabled"
            }

        finally:
            return result

    def fetch_transcripts(self, video_details: dict[str, list]) -> dict:
        """
        Fetches YouTube video transcripts for a list of videos organized by channel.

        Args:
            video_details (dict): A dictionary with channel_id as key and list of video_ids as value.
            languages (list): A list of language codes to fetch the transcripts.

        Returns:
            dict: A dictionary containing the fetched transcripts organized by channel.
        """
        try:                

            for channel_id, video_id_list in video_details.items():
                transcripts = {}
                for id in video_id_list:
                    result = self._fetch(id, channel_id)
                    transcripts[id] = result
                
                self.video_transcripts[channel_id] = transcripts

            return self.video_transcripts     
            
        except Exception as e:
            logger.error(f"Error fetching transcript for {id if id else channel_id}: {e}")
            logger.exception("Transcript save error:")
            return None

    def save_transcript(self, transcript_data: FetchedTranscript, channel_id: str, filename: str) -> str:
        """
        Saves transcript data to a JSON file.

        Args:
            transcript_data (FetchedTranscript): The fetched transcript data.
            channel_id (str): The channel ID for organizing storage.
            filename (str): The filename to save the transcript.

        Returns:
            str: The filepath of the saved transcript.
        """
        if not transcript_data:
            return False
        
        formatter = JSONFormatter()
        formatted_transcript = formatter.format_transcript(transcript_data)
            
        filepath = os.path.join(self.db.transcript_dir, channel_id, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(formatted_transcript)
            return filepath
        
        except Exception as e:
            logger.error(f"Error saving transcript for {filename}")
            logger.exception("Transcript save error:")
            return False