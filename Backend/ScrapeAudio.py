import yt_dlp

class Audio():
    def __init__(self, video_url=None):
        self.video_url = video_url
        pass

    def download_audio(self, output_path="./audio/"):

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path + '%(title)s.%(ext)s',
            'postprocessors': [],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print('video url', self.video_url)
            ydl.download([self.video_url])
            info = ydl.extract_info(self.video_url, download=False)
            return output_path + '%(title)s.%(ext)s'   