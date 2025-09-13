KNOWN ISSUE:

1. 
Traceback (most recent call last):
  File "D:\Personal\Personal_Projects\youtube_transcription_analysis\UI\MainWindow.py", line 157, in scrape_videos
    self.content = videos.fetch_video_urls(channel_url)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Personal\Personal_Projects\youtube_transcription_analysis\Backend\ScrapeVideo.py", line 45, in fetch_video_urls
    for live_entry,i in video_entries:
        ^^^^^^^^^^^^
ValueError: too many values to unpack (expected 2)

2.
terminal: {}
self.videos printing empty, did not dig through