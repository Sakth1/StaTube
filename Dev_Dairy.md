KNOWN ISSUE:

Traceback (most recent call last):
  File "D:\Personal\Personal_Projects\youtube_transcription_analysis\UI\MainWindow.py", line 157, in scrape_transcription
    transcripts = transcription.get_transcript(id)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Personal\Personal_Projects\youtube_transcription_analysis\Backend\ScrapeTranscription.py", line 10, in get_transcript
    self.transcript = transcriptAPI.fetch(video_id)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "d:\Personal\Personal_Projects\youtube_transcription_analysis\venv\Lib\site-packages\youtube_transcript_api\_api.py", line 72, in fetch
    .find_transcript(languages)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "d:\Personal\Personal_Projects\youtube_transcription_analysis\venv\Lib\site-packages\youtube_transcript_api\_transcripts.py", line 269, in find_transcript       
    return self._find_transcript(
           ^^^^^^^^^^^^^^^^^^^^^^
  File "d:\Personal\Personal_Projects\youtube_transcription_analysis\venv\Lib\site-packages\youtube_transcript_api\_transcripts.py", line 310, in _find_transcript      
    raise NoTranscriptFound(self.video_id, language_codes, self)
youtube_transcript_api._errors.NoTranscriptFound:
Could not retrieve a transcript for the video https://www.youtube.com/watch?v=vaWvHKj1pos! This is most likely caused by:

No transcripts were found for any of the requested language codes: ('en',)

For this video (vaWvHKj1pos) transcripts are available in the following languages:

(MANUALLY CREATED)
None

(GENERATED)
 - hi ("Hindi (auto-generated)")

(TRANSLATION LANGUAGES)
None

If you are sure that the described cause is not responsible for this error and that a transcript should be retrievable, please create an issue at https://github.com/jdepoix/youtube-transcript-api/issues. Please add which version of youtube_transcript_api you are using and provide the information needed to replicate the error. Also make sure that there are no open issues which already describe your problem!