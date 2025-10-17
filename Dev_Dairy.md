work on displaying profile pic in list widget

Change it so that the transcriptions is download for any language

fix this:
Exception in thread Thread-3 (search_thread):
Traceback (most recent call last):
  File "C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\threading.py", line 1075, in _bootstrap_inner
    self.run()
  File "C:\Users\HP\AppData\Local\Programs\Python\Python312\Lib\threading.py", line 1012, in run
    self._target(*self._args, **self._kwargs)
  File "d:\Personal\Personal_Projects\youtube_transcription_analysis\UI\MainWindow.py", line 118, in search_thread
    self.channels = search.search_channel(query)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "d:\Personal\Personal_Projects\youtube_transcription_analysis\Backend\ScrapeChannel.py", line 50, in search_channel
    self.db.insert(
  File "d:\Personal\Personal_Projects\youtube_transcription_analysis\Data\DatabaseManager.py", line 100, in insert
    cursor.execute(query, values)
sqlite3.OperationalError: table CHANNEL has no column named channel_id

have a look at thi proxy system:
import asyncio
from proxybroker import Broker

async def show(proxies):
    while True:
        proxy = await proxies.get()
        if proxy is None: break
        print('Found proxy: %s' % proxy)

proxies = asyncio.Queue()
broker = Broker(proxies)
tasks = asyncio.gather(
    broker.find(types=['HTTP', 'HTTPS'], limit=10),
    show(proxies))

loop = asyncio.get_event_loop()
loop.run_until_complete(tasks)