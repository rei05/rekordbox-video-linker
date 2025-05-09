import ssl
import time

import streamlit as st
from streamlit import session_state as ss
from streamlit_sortables import sort_items

from rekordbox_utils import (
    FileType,
    RekordboxDB,
    close_rekordbox,
    download_key,
    start_rekordbox,
)

# SSL認証に関するエラーを回避するための設定
# https://qiita.com/DisneyAladdin/items/9733a7e640a175c23f39
# https://hosochin.com/2022/05/03/post-1105/
ssl._create_default_https_context = ssl._create_unverified_context

class Content():
    def __init__(self, file_types):
        self.file_types = file_types
        self.playlists = []
        self.playlist_names = []
        self.playlist = None
        self.contents = []
        self.titles = []
        self.get_playlists()

    def get_playlists(self):
        self.playlists = db.get_playlists()
        self.playlists = self.file_types_filter(self.file_types)
        self.playlist_names = list(map(lambda x: x.Name, self.playlists))

    def get_contents(self, sort_type="trackno"):
        self.contents = db.get_playlist_contents(self.playlist, sort_type=sort_type)
        self.titles = [content.Title for content in self.contents]

    def sort_contents(self):
        self.titles.sort()
        self.contents.sort(key=lambda x: x.Title)

    def is_linked(self, contents):
        return db.is_linked(self.contents, contents)
    
    def link(self, contents):
        db.link(self.contents, contents)
        update_db()

    def unlink(self):
        db.unlink(self.contents)
        update_db()

    def reset(self):
        self.playlist = None
        self.contents = []
        self.titles = []

    # 指定した種類のファイルを含むプレイリストのみ抽出
    def file_types_filter(self, file_types):
        return list(filter(lambda x: db.is_contain_file_types(x, file_types), self.playlists))


def init_db():
    key = download_key()
    return RekordboxDB(key=key)

def update_db():
    close_rekordbox()
    db.commit()
    start_rekordbox()

def rekordbox_restart_count():
    with st.spinner("rekordboxを再起動中...", show_time=True):
        time.sleep(10)

@st.dialog("確認")
def link(sorted_video_contents):
    text_placeholder = st.empty()
    text_placeholder.write("rekordboxを再起動し動画をリンクします")
 
    columns_placeholder = st.empty()
    col1, col2 = columns_placeholder.columns(2) 
    with col1:
        if st.button("実行"):
            ss.link_exec_button = True
    with col2:
        if st.button("キャンセル"):
            st.rerun()

    if ss.link_exec_button:
        columns_placeholder.empty()
        text_placeholder.empty()
        ss.song.link(sorted_video_contents)
        rekordbox_restart_count()
        st.rerun()

@st.dialog("確認")
def unlink():
    text_placeholder = st.empty()
    text_placeholder.write("rekordboxを再起動し動画のリンクを解除します")
 
    columns_placeholder = st.empty()
    col1, col2 = columns_placeholder.columns(2) 
    with col1:
        if st.button("実行"):
            ss.link_exec_button = True
    with col2:
        if st.button("キャンセル"):
            st.rerun()

    if ss.link_exec_button:
        columns_placeholder.empty()
        text_placeholder.empty()
        ss.song.unlink()
        rekordbox_restart_count()
        st.rerun()

@st.fragment
def main():

    # セッションの初期化
    if "page" not in ss:
        ss.page = "page1"
    if "ready_to_link" not in ss:
        ss.ready_to_link = False
    if "ready_to_load" not in ss:
        ss.ready_to_load = False
    if "show_dialog" not in ss:
        ss.show_dialog = False
    if "selected_song_playlist_index" not in ss:
        ss.selected_song_playlist_index = None
    if "selected_video_playlist_index" not in ss:
        ss.selected_video_playlist_index = None
    if "dialog_result" not in ss:
        ss.dialog_result = None
    if "song" not in ss:
        ss.song = song
    if "video" not in ss:
        ss.video = video
    if "dummy_count" not in ss:
        ss.dummy_count = 0
    if "sorted_video_contents" not in ss:
        ss.sorted_video_contents = []
    if "link_exec_button" not in ss:
        ss.link_exec_button = False

    # ページ切り替え用関数
    def go_to_page(page_name):
        ss.page = page_name
        st.rerun()

    st.title("RekordboxVideoLinker")

    if ss.page == "page1":

        # プレイリスト選択
        col1, col2 = st.columns(2)
        with col1:
            selected = st.selectbox("①楽曲プレイリストを選んでください", ss.song.playlist_names, 
                                    index=ss.selected_song_playlist_index, placeholder="未選択")
            if selected is not None:
                ss.selected_song_playlist_index = ss.song.playlist_names.index(selected)
        with col2:
            selected = st.selectbox("②動画プレイリストを選んでください", ss.video.playlist_names, 
                                    index=ss.selected_video_playlist_index, placeholder="未選択")
            if selected is not None:
                ss.selected_video_playlist_index = ss.video.playlist_names.index(selected)

        if ss.selected_song_playlist_index is not None and ss.selected_video_playlist_index is not None:
            ss.ready_to_load = True

        # プレイリスト内のコンテンツ取得
        def get_contents(song_playlist_index, video_playlist_index):
            ss.song.playlist = ss.song.playlists[song_playlist_index]
            ss.video.playlist = ss.video.playlists[video_playlist_index]
            ss.song.get_contents(sort_type="trackno")
            ss.video.get_contents(sort_type="title")
            ss.ready_to_link = True

        # 「プレイリスト読み込み」ボタンの配置
        if ss.ready_to_load:
            if st.button("③プレイリスト読み込み", on_click=get_contents, 
                args=(ss.selected_song_playlist_index, ss.selected_video_playlist_index), use_container_width=True):
                go_to_page("page2")


    if ss.page == "page2":

        # プレイリストに含まれるコンテンツ一覧
        if ss.ready_to_link:

            st.write("④動画の順序を並び替えてください")

            col1, col2, col3 = st.columns([1, 0.2, 1])
            with col1:
                # 楽曲一覧
                st.write("楽曲")
                with st.spinner("楽曲ファイルをロード中..."):
                    html_text = """<div style="padding: 10px;"><div style="padding: 3px;">"""
                    for i, title in enumerate(ss.song.titles, 1):
                        html_text += f"""
                        <div style="border:1px solid #ccc; border-radius:.25rem; padding:.375rem .75rem; margin:5px; height: 2rem; 
                        display: flex; align-items: center; justify-content: flex-start; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">
                            <p style="margin: 0; text-align: left; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">{i:02d} {title}</p>
                        </div>"""
                    html_text += """</div></div>"""
                    st.markdown(html_text, unsafe_allow_html=True)

            with col2:
                # 楽曲ごとのリンク状況
                st.write("LINK状況")
                link_status_placeholder = st.empty()

            with col3:
                # 動画一覧
                st.write("動画")

                with st.spinner("動画ファイルをロード中..."):
                    custom_style = ".sortable-item {text-align: left; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;}"
                    sorted_video_titles = sort_items(ss.video.titles, direction='vertical', custom_style=custom_style)
                    ss.sorted_video_contents = [ss.video.contents[ss.video.titles.index(title)] for title in sorted_video_titles]

                # 楽曲ごとのリンク状況
                html_text = """<div style="padding: 10px;"><div style="padding: 3px;">"""
                for i, link_status in enumerate(ss.song.is_linked(ss.sorted_video_contents), 1):
                    link_status_icon = "✅️" if link_status else "❌️"
                    html_text += f"""
                    <div style="border:1px solid #ccc; border-radius:.25rem; padding:.375rem .75rem; margin:5px; height: 2rem; 
                    display: flex; align-items: center; justify-content: center;">
                        <p style="margin: 0;;">{link_status_icon}</p>
                    </div>"""
                html_text += """</div></div>"""
                link_status_placeholder.markdown(html_text, unsafe_allow_html=True)

        # セッションのリセット
        def reset():
            ss.song.reset()
            ss.video.reset()
            ss.clear()
            st.rerun()

        # ダミーを追加
        def add_dummy():
            ss.dummy_count += 1
            ss.video.contents.append(None)
            ss.video.titles.append(f"■■ Dummy Block {ss.dummy_count:02d} ■■")


        # ボタンの配置
        if ss.ready_to_link:
            col1, col2 = st.columns([1, 1])
            with col1:
                # リンク状況の表示
                if all(ss.song.is_linked(ss.sorted_video_contents)):
                    st.success('すべての楽曲に動画がリンクされています', icon="✅")
                else:
                    st.warning('1つ以上の楽曲に動画がリンクされていません', icon="⚠️")
            with col2:
                st.button("ダミーブロックを追加", on_click=add_dummy, use_container_width=True)

            col1, col2 = st.columns([0.3, 0.7])
            with col1:
                st.button("リンク解除", on_click=unlink, use_container_width=True)
            with col2:
                st.button("⑤リンク", on_click=link, args=([ss.sorted_video_contents]), use_container_width=True)
            
            st.button("⑥すべての表示をリセット", on_click=reset, use_container_width=True)


if __name__ == "__main__":
    db = init_db()

    SONG_FILE_TYPES = [FileType.MP3, FileType.M4A, FileType.FLAC, FileType.WAV, FileType.AIFF]
    VIDEO_FILE_TYPES = [FileType.MP4]

    song = Content(SONG_FILE_TYPES)
    video = Content(VIDEO_FILE_TYPES)

    st.set_page_config(layout="wide")

    main()
