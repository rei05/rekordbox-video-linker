import os
import sys
from pyrekordbox import Rekordbox6Database
from tabulate import tabulate

# プレイリストのTrackNo順にソートする
def sort_by_trackno(songPlaylists):
    content_trackno = {songPlaylist.TrackNo: songPlaylist.Content for songPlaylist in songPlaylists}
    sorted_content_trackno = sorted(content_trackno.items())
    return [content for _, content in sorted_content_trackno]

# プレイリストからコンテンツ情報を取得する
def get_playlist_contents(self, playlist_name):

    # プレイリストを取得
    playlist = self.get_playlist(Name=playlist_name).one()

    # プレイリスト内のコンテンツ情報を取得
    songPlaylists = self.get_playlist_songs(Playlist=playlist).all()

    # TrackNo順にソート
    contents = sort_by_trackno(songPlaylists)

    return contents

def main(db, song_playlist_name):
    try:
        print(f"{song_playlist_name=}")
        songs = db.get_playlist_contents(song_playlist_name)
    except:
        exit("[ERROR] 楽曲プレイリストを取得できませんでした。")

    try:
        table = []
        for i, song in enumerate(songs):
            song.VideoAssociate = None
            table.append([i+1, song.Title])
        db_commit_message = db.commit()
        print(tabulate(table, headers=["TrackNo", "Song"], tablefmt="grid"))
        print("[INFO] LINK解除成功。")
        input("[INFO] Enterキーを押すとコンソールログをクリアして終了します。")
        os.system("clear")
    except:
        print(db_commit_message)
        exit("[ERROR] LINK解除に失敗しました。")


if __name__ == "__main__":
    
    if len(sys.argv) != 2:
        exit("[ERROR] Usage: python unlink.py <楽曲プレイリスト名>")

    Rekordbox6Database.get_playlist_contents = get_playlist_contents
    db = Rekordbox6Database()

    main(db, sys.argv[1])
