from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
import json
import os

class SimpleYouTubeTranscriptFetcher:
    """
    A simplified class to fetch YouTube video transcripts using youtube-transcript-api.
    """
    
    def __init__(self, output_dir="transcripts"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_transcript(self, video_id, languages=('en',)):
        """
        Fetches a transcript for a single YouTube video.
        
        Args:
            video_id (str): The YouTube video ID.
            languages (tuple): A tuple of language codes to try (e.g., ('en', 'es')).
            
        Returns:
            dict: The transcript data and metadata, or None if failed.
        """
        try:
            transcript_list = YouTubeTranscriptApi().list(video_id=video_id)
            
            # Try to get a manual transcript first, fall back to generated
            try:
                transcript = transcript_list.find_manually_created_transcript(languages)
            except NoTranscriptFound:
                transcript = transcript_list.find_generated_transcript(languages)
            
            transcript_data = transcript.fetch()
            transcript_data = transcript_data.to_raw_data()
            print(transcript_data)
            
            # Structure the result
            result = {
                'video_id': video_id,
                'transcript': transcript_data,
                'language': transcript.language_code,
                'is_generated': transcript.is_generated
            }
            return result
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error fetching transcript for {video_id}: {e}")
            return None

    def save_transcript(self, transcript_data):
        """Saves transcript data to a JSON file."""
        if not transcript_data:
            return False
            
        video_id = transcript_data['video_id']
        filename = f"{video_id}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            print(f"Transcript saved to: {filepath}")
            return True
        except Exception as e:
            print(f"Error saving transcript for {video_id}: {e}")
            return False

# Example usage
if __name__ == "__main__":
    fetcher = SimpleYouTubeTranscriptFetcher()
    
    # Test with a video ID
    video_id = "dQw4w9WgXcQ"
    transcript = fetcher.fetch_transcript(video_id)
    
    if transcript:
        fetcher.save_transcript(transcript)