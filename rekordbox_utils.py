import io
from pathlib import Path
import sys
import re
import subprocess
import time
import urllib.request
import platform
from enum import IntEnum

from pyrekordbox import Rekordbox6Database, show_config
from pyrekordbox.db6.tables import DjmdContent, DjmdPlaylist


class FileType(IntEnum):
    MP3 = 1
    MP4 = 3
    M4A = 4
    FLAC = 5
    WAV = 11
    AIFF = 12


class RekordboxDB(Rekordbox6Database):
    def __init__(self, key):
        super().__init__(key=key)

    def sort_by_name(self, playlists):
        sorted_indices = argsort(list(map(lambda x: x.Name, playlists)))
        return [playlists[i] for i in sorted_indices]

    def sort_by_title(self, songs):
        sorted_indices = argsort(list(map(lambda x: x.Content.Title, songs)))
        return [songs[i] for i in sorted_indices]

    def sort_by_trackno(self, songs):
        sorted_indices = argsort(list(map(lambda x: x.TrackNo, songs)))
        return [songs[i] for i in sorted_indices]

    def get_playlists(self):
        playlists = self.get_playlist().all()
        return self.sort_by_name(playlists)

    def get_playlist_contents(self, playlist, sort_type="trackno"):
        songs = self.get_playlist_songs(Playlist=playlist).all()
        if sort_type == "title":
            return list(map(lambda x: x.Content, self.sort_by_title(songs)))
        elif sort_type == "trackno":
            return list(map(lambda x: x.Content, self.sort_by_trackno(songs)))
        else:
            raise ValueError("Invalid sort type. Use 'title' or 'trackno'.")
    
    def link(self, songs, videos):
        target_videos = fit_list_len(songs, videos)
        for song, video in zip(songs, target_videos):
            video_id = video.ID if video is not None else None
            song.VideoAssociate = video_id

    def unlink(self, songs):
        for song in songs:
            song.VideoAssociate = None

    def is_linked(self, songs, videos):
        target_videos = fit_list_len(songs, videos)
        is_linked_list = []
        for song, video in zip(songs, target_videos):
            if song.VideoAssociate is None:
                is_linked_list.append(False)
                continue
            video_id = video.ID if video is not None else None
            is_linked_list.append(song.VideoAssociate == video_id)
        return is_linked_list
    
    def is_contain_file_types(self, playlist, target_file_types):
        contents = self.get_playlist_contents(playlist)
        return any([FileType(int(content.FileType)) in target_file_types for content in contents])


def argsort(sequence):
    return sorted(range(len(sequence)), key=lambda x: sequence[x])

def fit_list_len(list1, list2):
    if len(list1) < len(list2):
        return list2[:len(list1)]
    if len(list1) > len(list2):
        return list2 + [None] * (len(list1)-len(list2))
    return list2

def is_rekordbox_running():
    if platform.system() == "Windows":
        result = subprocess.run(['tasklist'], stdout=subprocess.PIPE, text=True)
        return "rekordbox.exe" in result.stdout
    else:
        result = subprocess.run(['pgrep', '-fl', 'rekordbox'], stdout=subprocess.PIPE)
        return True if result.stdout else False

def close_rekordbox():
    if is_rekordbox_running():
        if platform.system() == "Windows":
            subprocess.run(['taskkill', '/IM', 'rekordbox.exe', '/F'])
        else:
            subprocess.run(['pkill', 'rekordbox'])
        
        timeout = 10
        elapsed_time = 0
        while is_rekordbox_running() and elapsed_time < timeout:
            time.sleep(1)
            elapsed_time += 1
        if elapsed_time >= timeout:
            exit("[Error] rekordboxの終了がタイムアウトしました。")

def start_rekordbox():
    if platform.system() == "Windows":
        rekordbox_path = get_rekordbox_path()
        subprocess.Popen([rekordbox_path / 'rekordbox.exe'])
    else:
        subprocess.run(['open', '-a', 'rekordbox'])

# rekordbox.exeのパスを取得する
def get_rekordbox_path():

    # 標準出力をキャプチャするためのオブジェクトを作成
    buffer = io.StringIO()
    # 標準出力をbufferに切り替え
    sys.stdout = buffer
    # printの内容をキャプチャ
    show_config()
    # 標準出力を元に戻す
    sys.stdout = sys.__stdout__
    # bufferの内容を取得
    config_text = buffer.getvalue()

    for line in config_text.splitlines()[::-1]:
        if "install_dir" in line:
            return Path(line.split("=")[-1].strip())

def download_key():

    KEY_SOURCES = [
        {
            "url": r"https://raw.githubusercontent.com/mganss/CueGen/19878e6eb3f586dee0eb3eb4f2ce3ef18309de9d/CueGen/Generator.cs",  # noqa: E501
            "regex": re.compile(
                r'((.|\n)*)Config\.UseSqlCipher.*\?.*"(?P<dp>.*)".*:.*null',
                flags=re.IGNORECASE | re.MULTILINE,
            ),
        },
        {
            "url": r"https://raw.githubusercontent.com/dvcrn/go-rekordbox/8be6191ba198ed7abd4ad6406d177ed7b4f749b5/cmd/getencryptionkey/main.go",  # noqa: E501
            "regex": re.compile(
                r'((.|\n)*)fmt\.Print\("(?P<dp>.*)"\)', flags=re.IGNORECASE | re.MULTILINE
            ),
        },
    ]

    dp = ""
    for source in KEY_SOURCES:
        url = source["url"]
        regex = source["regex"]
        print(f"Looking for key: {url}")

        res = urllib.request.urlopen(url)
        data = res.read().decode("utf-8")
        match = regex.match(data)
        if match:
            dp = match.group("dp")
            break
    if dp:
        return dp
    else:
        print("No key found in the online sources.")

