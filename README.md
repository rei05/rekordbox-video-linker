# rekordbox-video-linker

- rekordboxのビデオLINKを自動化するやつ
- 楽曲プレイリストと動画プレイリストを指定するとTrackNo順に一括でLINKしてくれるよ
- MacOSのみ対応

# 事前準備

## 1. rekordbox 6の導入
- 本ツールで使用しているライブラリ"[pyrekordbox](https://github.com/dylanljones/pyrekordbox)"はrekordboxバージョン5または6しか対応していないためバージョン7を使っている場合は6を導入する。
  - なお、6と7は同じPCに共存することができ、内部データベースも共有しているっぽいので、本ツールを使いながら**今まで通りバージョン7を使い続けることが可能。**
- rekordboxバージョン6のインストールは[こちら](https://support.pioneerdj.com/hc/ja/articles/8112764645785-rekordbox-ver-6-%E3%82%A4%E3%83%B3%E3%82%B9%E3%83%88%E3%83%BC%E3%83%AB%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB%E3%82%A2%E3%83%BC%E3%82%AB%E3%82%A4%E3%83%96)から。

## 2. 楽曲と動画の準備
- 好きな楽曲を入れたプレイリストを用意する
- 楽曲とは別にプレイリストを作成し、各楽曲に対応する動画ファイルを追加する。
- このとき、楽曲・動画ともに、プレイリスト内のTrackNoが演奏順になるよう並べておく。
  - ファイル名の先頭に01_, 02_,...と付けるなど演奏順でファイル名ソートできるようにしておくと便利。
- 楽曲数と動画数は一致している必要がある。

# 環境構築(初回のみ)

## 1. このリポジトリをclone

```sh
git clone https://github.com/rei05/rekordbox-video-linker
cd rekordbox-video-linker
```

## 2. 仮想環境作成

- なくてもいい

```sh
python -m venv venv
. venv/bin/activate
```

## 3. pyrekordboxとその他必要ライブラリの導入

- import [pyrekordbox](https://github.com/dylanljones/pyrekordbox) as god...

```sh
pip install setuptools pyrekordbox tabulate
```

## 4. SQLCipherの導入

- 後述のsqlcipher3をビルドするために必要
- [Homebrew](https://brew.sh/ja/)が未導入の場合は先に入れておく

```sh
brew install SQLCipher
```

## 5. sqlcipher3の導入

- rekordboxの内部データベース(master.db)の暗号化を解くためのもの

```sh
git clone https://github.com/coleifer/sqlcipher3
git clone https://github.com/geekbrother/sqlcipher-amalgamation
cd sqlcipher3
SQLCIPHER_PATH=$(brew --prefix sqlcipher); C_INCLUDE_PATH="$SQLCIPHER_PATH"/include LIBRARY_PATH="$SQLCIPHER_PATH"/lib python setup.py build
SQLCIPHER_PATH=$(brew --prefix sqlcipher); C_INCLUDE_PATH="$SQLCIPHER_PATH"/include LIBRARY_PATH="$SQLCIPHER_PATH"/lib python setup.py install
SQLCIPHER_PATH=$(brew --prefix sqlcipher); C_INCLUDE_PATH="$SQLCIPHER_PATH"/include LIBRARY_PATH="$SQLCIPHER_PATH"/lib python setup.py install
cd ../
```
- 同じコマンドを2回実行しているのは、なんか2回やるとうまくいく知らんけど。
- 下記のような出力になれば成功。

```sh
(前略)
Finished processing dependencies for sqlcipher3==0.5.4
```

- `Finished processing 〜`ではなく`error: 〜`と出る場合は、sqlcipher3のビルドに失敗している可能性あり。

## 6. 復号化keyの取得

- master.dbを復号化するためのキーを取得しキャッシュに保存する

```sh
python -m pyrekordbox download-key
```

## 7. rekordbox検出の確認

- pyrekordboxがPCにインストールされているrekordbox 6を検出できているか確認

```sh
python show_config.py
```

- 下記のような出力になればOK。

```
Pioneer:
   app_dir =      /Users/<username>/Library/Application Support/Pioneer
   install_dir =  /Applications
Rekordbox 5:
Rekordbox 6:
   app_dir =      /Users/<username>/Library/Application Support/Pioneer/rekordbox6
   db_dir =       /Users/<username>/Library/Pioneer/rekordbox
   db_path =      /Users/<username>/Library/Pioneer/rekordbox/master.db
   install_dir =  /Applications/rekordbox 6
   version =      6
```

- `Rekordbox 6:`の項目が空になっている場合、rekordboxバージョン6のインストールフォルダの検出に失敗している可能性あり。

# 使い方

- rekordboxが起動している場合は必ず終了する。
  - 起動したままだと「LINK失敗」と表示される。
  - アプリ終了操作をしてから完全にタスクkillされるまで数秒かかる場合がある。
- 以下のコマンドを実行。

```sh
python link.py <楽曲プレイリスト名> <動画プレイリスト名> 
```

- うまく行けば、LINKされた楽曲と動画の組が一覧で出力される。
- rekordboxを起動すると指定したプレイリスト内の楽曲全てに動画がLINKされているはず。
