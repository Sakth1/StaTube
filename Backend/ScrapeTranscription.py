from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, FetchedTranscript, TranscriptsDisabled
from youtube_transcript_api.formatters import JSONFormatter
import json
import os

from Data.DatabaseManager import DatabaseManager
from utils.AppState import app_state

class TranscriptFetcher:
    """
    A simplified class to fetch YouTube video transcripts using youtube-transcript-api.
    """
    def __init__(self):
        self.db: DatabaseManager = app_state.db
        self.video_transcripts: dict = {}

    def _fetch(self, video_id, channel_id, language_option=("en",)):
        # Try to get a manual transcript first, fall back to generated
        try:
            transcript_list = YouTubeTranscriptApi().list(video_id=video_id)
            try:
                transcript = transcript_list.find_manually_created_transcript(language_codes=language_option)
            except NoTranscriptFound:
                transcript = transcript_list.find_generated_transcript(language_codes=language_option)
            
            transcript_data = transcript.fetch()
            filename = f"{video_id}.json"
            filepath = self.save_transcript(transcript_data, channel_id, filename)            
            # Structure the result
            result = {
                'video_id': video_id,
                'filepath': filepath,
                'language': transcript.language_code,
                'is_generated': transcript.is_generated
            }
        
        except TranscriptsDisabled:
            print(f"Transcripts disabled for {video_id}")
            result = None

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error fetching transcript for {video_id}: {e}")
            result = None

        finally:
            return result
        
    def fetch_transcripts(self, video_details: dict[str, list], languages: list = ["en"]):
        try:                
            if len(languages) > 1:
                language_option = tuple(l for l in languages) + (languages[0],)
            else:
                language_option = (languages[0],)

            for channel_id, video_id_list in video_details.items():
                transcripts = {}
                for id in video_id_list:
                    result = self._fetch(id, channel_id, language_option)
                    if result is not None:
                        transcripts[id] = result
                
                self.video_transcripts[channel_id] = transcripts

            return self.video_transcripts     
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error fetching transcript for {id if id else channel_id}: {e}")
            return None

    def save_transcript(self, transcript_data:FetchedTranscript, channel_id:str, filename:str):
        """Saves transcript data to a JSON file."""
        if not transcript_data:
            return False
        
        formatter = JSONFormatter()
        formatted_transcript = formatter.format_transcript(transcript_data)
            
        filepath = os.path.join(self.db.transcript_dir, channel_id, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(formatted_transcript)
            print(f"Transcript saved to: {filepath}")
            return filepath
        
        except Exception as e:
            print(f"Error saving transcript for {id}: {e}")
            return False
