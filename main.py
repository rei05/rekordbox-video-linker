import sys
import time

from PySide6.QtCore import QStringListModel, Qt, QThread
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from rekordbox_utils import (
    FileType,
    RekordboxDB,
    close_rekordbox,
    create_blank_content,
    download_key,
    init_playlist,
    start_rekordbox,
)

BLANK = "--------BLANK--------"


class Content():
    def __init__(self, main_window, name, file_types):
        self.main_window = main_window
        self.file_types = file_types
        self.playlists = []
        self.playlist_names = []
        self.playlists_view = QListView()
        self.playlist = init_playlist(name)
        self.selected_playlist_label = QLabel(self.playlist.Name)
        self.contents_view = QListWidget()
        self.contents = []
        self.titles = []

    def get_playlists(self):
        self.playlists = db.get_playlists()
        self.playlists = self.file_types_filter(self.file_types)
        self.playlist_names = list(map(lambda x: x.Name, self.playlists))

    def create_playlists_view(self):
        self.playlists_view.setModel(QStringListModel(self.playlist_names))
        self.playlists_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.playlists_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.playlists_view.doubleClicked.connect(self.update_contents_view)

    def update_contents_view(self):
        selected_indexes = self.playlists_view.selectedIndexes()
        self.playlist = self.playlists[selected_indexes[0].row()]
        self.selected_playlist_label.setText(self.playlist.Name)
        self.contents = db.get_playlist_contents(self.playlist)
        self.titles = [content.Title for content in self.contents]
        self.contents_view.clear()
        self.contents_view.addItems(self.titles)
        self.main_window.update_link_status()

    def sort_contents(self):
        self.contents_view.sortItems()
        self.main_window.update_link_status()

    def setDragDropMode(self):
        self.contents_view.setDragDropMode(QListWidget.InternalMove)

    # コンテンツの並び順を取得する
    def get_contents_order(self):
        n_contents = self.contents_view.count()
        titles = [self.contents_view.item(i).text() for i in range(n_contents)]
        sorted_contents = []
        for title in titles:
            for content in self.contents:
                if content.Title != title: continue
                sorted_contents.append(content)
                break
        return sorted_contents

    # 指定した種類のファイルを含むプレイリストのみ抽出
    def file_types_filter(self, file_types):
        return list(filter(lambda x: db.is_contain_file_types(x, file_types), self.playlists))


# テキストを中央揃えにする設定(LINKステータス用)
class CenterAlignedStringListModel(QStringListModel):
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        return super().data(index, role)

# メインUI
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rekordbox Video Linker")

        song_file_types = [FileType.MP3, FileType.M4A, FileType.FLAC, FileType.WAV, FileType.AIFF]
        video_file_types = [FileType.MP4]

        self.song = Content(self, "楽曲", song_file_types)
        self.video = Content(self, "動画", video_file_types)

        self.song.get_playlists()
        self.video.get_playlists()

        self.song.create_playlists_view()
        self.video.create_playlists_view()

        self.video.setDragDropMode()

        self.link_status_model = CenterAlignedStringListModel([])
        self.update_link_status()

        sort_button = QPushButton("ファイル名ソート")
        sort_button.clicked.connect(self.video.sort_contents)

        self.link_status_view = QListView()
        self.link_status_view.setModel(self.link_status_model)
        self.link_status_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        add_blank_button = QPushButton("ブランク追加")
        add_blank_button.clicked.connect(self.add_blank)

        unlink_button = QPushButton("LINK解除")
        unlink_button.clicked.connect(self.unlink)

        link_button = QPushButton("LINK")
        link_button.clicked.connect(self.link)

        playlist_view_gridlayout = QGridLayout()
        playlist_view_gridlayout.addWidget(QLabel("楽曲(mp3)プレイリスト"), 0, 0)
        playlist_view_gridlayout.addWidget(QLabel("動画(mp4)プレイリスト"), 0, 1)
        playlist_view_gridlayout.addWidget(self.song.playlists_view, 1, 0)
        playlist_view_gridlayout.addWidget(self.video.playlists_view, 1, 1)

        videos_view_footer_gridlayout = QHBoxLayout()
        videos_view_footer_gridlayout.addWidget(sort_button)
        videos_view_footer_gridlayout.addWidget(add_blank_button)
        videos_view_footer_container = QWidget()
        videos_view_footer_container.setLayout(videos_view_footer_gridlayout)

        contents_view_gridlayout = QGridLayout()
        contents_view_gridlayout.addWidget(QLabel("▼"), 0, 0, alignment=Qt.AlignCenter)
        contents_view_gridlayout.addWidget(QLabel("▼"), 0, 2, alignment=Qt.AlignCenter)
        contents_view_gridlayout.addWidget(self.song.selected_playlist_label, 1, 0, alignment=Qt.AlignCenter)
        contents_view_gridlayout.addWidget(QLabel("LINKステータス"), 1, 1, alignment=Qt.AlignCenter)
        contents_view_gridlayout.addWidget(self.video.selected_playlist_label, 1, 2, alignment=Qt.AlignCenter)
        contents_view_gridlayout.addWidget(self.song.contents_view, 2, 0)
        contents_view_gridlayout.addWidget(self.link_status_view, 2, 1)
        contents_view_gridlayout.addWidget(self.video.contents_view, 2, 2)
        contents_view_gridlayout.addWidget(videos_view_footer_container, 3, 2)

        contents_view_gridlayout.setColumnStretch(0, 4)
        contents_view_gridlayout.setColumnStretch(1, 1)
        contents_view_gridlayout.setColumnStretch(2, 4)

        link_button_gridlayout = QGridLayout()
        link_button_gridlayout.addWidget(unlink_button, 0, 0)
        link_button_gridlayout.addWidget(link_button, 0, 1)

        layout = QVBoxLayout()
        layout.addLayout(playlist_view_gridlayout, 3)
        layout.addLayout(contents_view_gridlayout, 7)      
        layout.addLayout(link_button_gridlayout)
        self.setLayout(layout)


    # LINKステータスを更新する
    def update_link_status(self):
        self.song.contents = self.song.get_contents_order()
        self.video.contents = self.video.get_contents_order()
        if len(self.song.contents) == 0 or len(self.video.contents) == 0: return
        is_linked_list = db.is_linked(self.song.contents, self.video.contents)
        link_status = ["✅️" if is_linked else "❌️" for is_linked in is_linked_list]
        self.link_status_model.setStringList(link_status)

    # LINKする
    def link(self):
        self.song.contents = self.song.get_contents_order()
        self.video.contents = self.video.get_contents_order()
        db.link(self.song.contents, self.video.contents)
        self.update_db()
        self.update_link_status()
    
    # LINKを解除する
    def unlink(self):
        self.song.contents = self.song.get_contents_order()
        db.unlink(self.song.contents)
        self.update_db()
        self.update_link_status()

    def add_blank(self):
        self.video.contents_view.addItem(BLANK)
        self.video.contents.append(create_blank_content(BLANK))
        self.update_link_status()

    # rekordboxのmaster.dbに更新を反映する
    def update_db(self):
        popup = PopupWindow()
        popup.setModal(True)
        self.worker = WorkerThread(db)
        self.worker.finished.connect(popup.highlight_window)
        self.worker.start()
        popup.exec()
        self.raise_()

# rekordbox再起動の非同期処理
class WorkerThread(QThread):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def run(self):
        close_rekordbox()
        self.db.commit()
        start_rekordbox()

# rekordbox再起動時のポップアップウィンドウ
class PopupWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("rekordboxを再起動中...")
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()
        label = QLabel("rekordboxを再起動中...")
        label.setStyleSheet("color: red; font-size: 20px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        self.setLayout(layout)

    def highlight_window(self):
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        time.sleep(10)
        self.accept()


def init_db():
    key = download_key()
    return RekordboxDB(key=key)

if __name__ == "__main__":
    db = init_db()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(720, 1280)
    window.show()
    sys.exit(app.exec())
