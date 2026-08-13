import os

class BGMLibrary:
    def __init__(self, music_dir: str = "assets/music"):
        self.music_dir = music_dir
        os.makedirs(music_dir, exist_ok=True)

    def get_track(self, mood: str) -> str:
        if os.path.exists(self.music_dir):
            for file in os.listdir(self.music_dir):
                if mood.lower() in file.lower() and file.endswith((".mp3", ".wav")):
                    return os.path.join(self.music_dir, file)
        return "" 