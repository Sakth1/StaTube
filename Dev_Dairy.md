Change it so that the transcriptions is download for any language

fix this:
Exception has occurred: FileNotFoundError
[Errno 2] No such file or directory: 'C:\\Users\\HP\\Documents\\YTAnalysis\\Channels\\channel_UCG2CL6EUjG8TVT1Tpl9nJdg.json'
  File "D:\Personal\Personal_Projects\youtube_transcription_analysis\Data\DatabaseManager.py", line 134, in save_json_file
    with open(filepath, "w", encoding="utf-8") as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Personal\Personal_Projects\youtube_transcription_analysis\Backend\ScrapeChannel.py", line 28, in search_channel
    self.db.base_dir / "Channels",

                    f"channel_{channel_id}",

                    {"id": channel_id, "title": title, "url": url},

                )
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Personal\Personal_Projects\youtube_transcription_analysis\UI\MainWindow.py", line 108, in search_thread
    self.channels = search.search_channel(query)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\HP\\Documents\\YTAnalysis\\Channels\\channel_UCG2CL6EUjG8TVT1Tpl9nJdg.json'