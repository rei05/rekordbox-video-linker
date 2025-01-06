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

def main(db, song_playlist_name, video_playlist_name):
    try:
        print(f"{song_playlist_name=}")
        songs = db.get_playlist_contents(song_playlist_name)
    except:
        exit("[ERROR] 楽曲プレイリストを取得できませんでした。")

    try:
        print(f"{video_playlist_name=}")
        videos = db.get_playlist_contents(video_playlist_name)
    except:
        exit("[ERROR] 動画プレイリストを取得できませんでした。")

    if len(songs) != len(videos):
        input_ = input("[WARNING] 楽曲と動画の数が一致していません。無視して続行しますか？(y/n): ")
        if input_ != "y": exit()
        lesser_length = min(len(songs), len(videos))
        songs = songs[:lesser_length]
        videos = videos[:lesser_length]

    try:
        table = []
        for i, (song, video) in enumerate(zip(songs, videos)):
            song.VideoAssociate = video.ID
            table.append([i+1, song.Title, video.Title])
        db.commit()
        print("[INFO] LINK成功。")
        print(tabulate(table, headers=["TrackNo", "Song", "Video"], tablefmt="grid"))
    except:
        exit("[ERROR] LINKに失敗しました。")


if __name__ == "__main__":
    
    if len(sys.argv) != 3:
        exit("[ERROR] Usage: python link.py <楽曲プレイリスト名> <動画プレイリスト名>")

    Rekordbox6Database.get_playlist_contents = get_playlist_contents
    db = Rekordbox6Database()

    main(db, sys.argv[1], sys.argv[2])
