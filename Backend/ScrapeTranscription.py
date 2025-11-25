from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, FetchedTranscript, TranscriptsDisabled
from youtube_transcript_api.formatters import JSONFormatter
import json
import os
from PySide6.QtCore import QObject, Signal

from Data.DatabaseManager import DatabaseManager
from utils.AppState import app_state

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
        """
        try:
            total_videos = sum(len(v_list) for v_list in self.video_details.values())
            processed_count = 0
            
            self.progress_updated.emit("Starting transcript scrape...")
            self.progress_percentage.emit(0)

            language_option = ["en"]

            for channel_id, video_id_list in self.video_details.items():
                for video_id in video_id_list:
                    self.progress_updated.emit(f"Fetching transcript for {video_id}...")
                    
                    # Perform fetch
                    result = self.fetcher._fetch(video_id, channel_id, language_option)
                    
                    processed_count += 1
                    percentage = int((processed_count / total_videos) * 100)
                    self.progress_percentage.emit(percentage)
                    
                    if result.get("filepath"):
                        self.progress_updated.emit(f"Saved: {video_id}")
                    else:
                        self.progress_updated.emit(f"Skipped: {video_id} ({result.get('remarks')})")

            self.progress_updated.emit("Transcript scraping completed!")
            self.progress_percentage.emit(100)
            self.finished.emit()

        except Exception as e:
            import traceback
            traceback.print_exc()
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
            
            # Structure the result
            result = {
                'video_id': video_id,
                'filepath': filepath,
                'language': transcript.language_code,
                'is_generated': transcript.is_generated,
                'remarks': None
            }
        
        except TranscriptsDisabled:
            print(f"Transcripts disabled for {video_id}")
            result = {
                'video_id': video_id,
                'filepath': None,
                'language': None,
                'is_generated': None,
                'remarks': "Transcripts disabled"
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error fetching transcript for {video_id}: {e}")
            result = {
                'video_id': video_id,
                'filepath': None,
                'language': None,
                'is_generated': None,
                'remarks': "Transcripts disabled"
            }

        finally:
            return result

    def fetch_transcripts(self, video_details: dict[str, list], languages: list = ["en"]) -> dict:
        """
        Fetches YouTube video transcripts for a list of videos organized by channel.

        Args:
            video_details (dict): A dictionary with channel_id as key and list of video_ids as value.
            languages (list): A list of language codes to fetch the transcripts.

        Returns:
            dict: A dictionary containing the fetched transcripts organized by channel.
        """
        try:                
            language_option = ["en"]

            for channel_id, video_id_list in video_details.items():
                transcripts = {}
                for id in video_id_list:
                    result = self._fetch(id, channel_id, language_option)
                    if result.get("filepath") is None:
                        print(result.get("remarks"))
                    transcripts[id] = result
                
                self.video_transcripts[channel_id] = transcripts

            return self.video_transcripts     
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error fetching transcript for {id if id else channel_id}: {e}")
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
            print(f"Error saving transcript for {id}: {e}")
            return False