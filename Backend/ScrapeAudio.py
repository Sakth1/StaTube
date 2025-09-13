import yt_dlp

class Audio():
    def __init__(self):
        pass

    def download_audio(video_url:str, output_path="./audio/"):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path + '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',  # or 'mp3'
                'preferredquality': '192',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
            info = ydl.extract_info(video_url, download=False)
            return info['title']