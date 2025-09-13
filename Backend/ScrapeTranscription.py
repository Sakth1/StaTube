from youtube_transcript_api import YouTubeTranscriptApi


class Transcription:
    def __init__(self):
        self.transcript = None

    def get_transcript(self, video_id):
        transcriptAPI = YouTubeTranscriptApi()
        self.transcript = transcriptAPI.fetch(video_id)
        return self.transcript


