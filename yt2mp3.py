from __future__ import unicode_literals
import requests
import youtube_dl
import argparse
import os
import sys
import shutil
import ctypes
import time
from PIL import Image
from io import BytesIO
from pydub import AudioSegment
from mutagen.id3 import ID3, APIC
from mutagen.easyid3 import EasyID3
from PyQt5 import QtCore, QtGui, QtWidgets, QtMultimedia


class Song:
    def __init__(self, title, artist, yt_link, cover_art, central_widget, album=None):
        self.progress_bar = central_widget.findChild(QtWidgets.QProgressBar, "progressBar")
        self.title = title
        self.artist = artist
        self.album = album
        if not album:
            self.album = self.title.split('(')[0] + "- Single"
        self.full_song = "{} - {}".format(self.artist, self.title)
        self.mp3 = f"downloads/{self.full_song}.mp3"
        self.cover = cover_art

        self.download_yt(yt_link)
        self.set_progress({'status': 'converting'})
        self.set_tags()
        self.set_progress({'status': 'converted'})

    def download_yt(self, yt):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads//' + self.full_song + '.%(ext)s',
            'progress_hooks': [self.set_progress],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }]
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([yt])

    def set_tags(self):
        image = open(self.cover, 'rb').read()
        audio = EasyID3(self.mp3)
        audio['artist'] = self.artist
        audio['title'] = self.title
        audio['album'] = self.album
        audio['albumartist'] = self.artist
        audio.save(v2_version=3)

        audio = ID3(self.mp3)
        audio.add(APIC(3, 'image/jpeg', 3, 'Front cover', image))
        audio.save(v2_version=3)

    def set_progress(self, d):
        if d['status'] == 'finished':
            self.progress_bar.setValue(80)
        elif d['status'] == 'converting':
            self.progress_bar.setValue(90)
        elif d['status'] == 'converted':
            self.progress_bar.setValue(100)
        elif d['status'] == 'downloading':
            percentage = (int(d['downloaded_bytes']) / int(d['total_bytes'])) * 100
            self.progress_bar.setValue(percentage)


class SongPreviewPlayer(QtMultimedia.QMediaPlayer):
    def __init__(self, ins):
        super().__init__(ins)
        self.ins = ins
        self.initialized = False

        self.positionChanged.connect(self.position_changed_callback)
        self.setNotifyInterval(100)

    def init_preview_clip(self, mp3_file):
        if self.initialized:
            return
        preview_file = self.create_preview_clip(mp3_file, "data/preview", output_format='wav')
        content = QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(preview_file))
        self.setMedia(content)
        self.initialized = True

    def play_preview_clip(self, mp3_file):
        if not self.initialized:
            self.init_preview_clip(mp3_file)
        self.setPosition(0)
        self.play()

    @staticmethod
    def create_preview_clip(mp3_file, output_filename, output_format):
        sound = AudioSegment.from_mp3(mp3_file)

        output_file = f"{output_filename}.{output_format}"

        preview_point = len(sound) * 0.03
        preview_part = sound[preview_point * 5:preview_point * 6] - 15
        preview_part = preview_part.fade_in(500)
        preview_part = preview_part.fade_out(500)
        preview_part.export(output_file, format=output_format)

        return output_file

    def position_changed_callback(self, position):
        if self.initialized:
            if self.duration() != 0:
                progress_bar = self.ins.findChild(QtWidgets.QProgressBar, "progressBar")
                progress_value = (position / self.duration()) * 100
                progress_bar.setValue(progress_value)
                if self.duration() == position:
                    self.initialized = False
                    self.setMedia(QtMultimedia.QMediaContent(None))


class WidgetActions:
    def __init__(self, ins):
        self.ins = ins
        self.data = {}
        self.preview_player = SongPreviewPlayer(ins)
        self.data = {
            'YouTube': 'https://www.youtube.com/watch?v=Lu3LZmhC_DY',
            'Title': 'GAM GAM',
            'Artist': 'Marnik & SMACK',
            'Album': 'GAM GAM',
            'CoverArt': 'downloads/f.jpeg'
        }

    def is_single(self, checkbox, album_input):
        state = checkbox.checkState()
        if state == QtCore.Qt.Checked:
            self.add_data('isSingle', True)
            if self.data.get('Album'):
                del self.data['Album']
            album_input.clear()
            album_input.setDisabled(True)
        else:
            self.add_data('isSingle', False)
            album_input.setDisabled(False)

    def set_youtube_link(self, text):
        if text and text.startswith("https://www.youtube.com/watch?v="):
            self.add_data('YouTube', text)

    def add_data(self, name, value):
        if value is not None:
            self.data[name] = value
            print(f"{name}: {value}")

    def set_cover_art(self, cover_art):
        self.add_data('CoverArt', cover_art)

    def preview_song(self, init=False):
        if init:
            self.preview_player.init_preview_clip(self.data['mp3'])
            return
        self.preview_player.play_preview_clip(self.data['mp3'])

    def download(self):
        tags = ['Title', 'Artist', 'YouTube', 'Album', 'CoverArt']
        if self.data.get('isSingle'):
            tags.remove('Album')

        validate_tags = [self.data.get(tag) for tag in tags]
        if None in validate_tags:
            CreateWidgets.create_alert_popup_message(self.ins, "Alert", "Not all fields are filled")
            return
        song = Song(self.data['Title'], self.data['Artist'], self.data['YouTube'],
                    self.data['CoverArt'], self.ins, self.data.get('Album')
                    )
        self.data['mp3'] = song.mp3
        self.ins.findChild(QtWidgets.QPushButton, "previewSongButton").setDisabled(False)
        if self.data.get('instantPreview'):
            self.preview_song(init=True)
        elif self.data.get('instantPlay'):
            self.preview_song()

    @staticmethod
    def tag_fetch(fetch_method):
        '''NOT YET IMPLEMENTED'''
        print("Current fetching method: " + fetch_method)

    def new_song(self, tpe):
        if tpe == 0:
            for input in self.ins.findChildren(QtWidgets.QLineEdit):
                input.clear()

            image_viewer = [val for val in self.ins.findChildren(QtWidgets.QLabel) if val.objectName() == "coverArtPreview"][0]
            image_viewer.set_default_image()
            self.data = {}
            print("New song...")
        else:
            print("Bulk song download...")


class QImageViewer(QtWidgets.QLabel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.current_image = None
        self.setAcceptDrops(True)
        self.setScaledContents(True)
        self.setToolTip("Drag and drop cover art image here")
        self.set_default_image()

    def set_default_image(self):
        self.setPixmap(QtGui.QPixmap(QtGui.QImage('data/drophere.png')))

    def dragEnterEvent(self, e):
        m = e.mimeData()
        if m.hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        m = e.mimeData()
        if m.hasUrls():
            self.load_image(m.urls()[0].toLocalFile())

    def mousePressEvent(self, e):
        dialog = QtWidgets.QFileDialog(
            self,
            "Select cover art image",
            QtCore.QDir.currentPath(),
            "JPG files (*.jpg)"
        )
        if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
            self.load_image(dialog.selectedFiles()[0])

    def load_image(self, image_location):
        img = Image.open(image_location)
        self.current_image = "data/temp_cover.jpg"
        img.save(self.current_image, 'jpeg')
        _img = QtGui.QImage(image_location)
        _pixmap = QtGui.QPixmap(_img)
        self.setPixmap(_pixmap)
        self.callback(self.current_image)


class CreateWidgets:
    @staticmethod
    def create_button(ins, obj_name, text, action):
        btn = QtWidgets.QPushButton(ins)
        btn.setObjectName(obj_name)
        btn.setText(text)
        btn.clicked.connect(action)
        return btn

    @staticmethod
    def create_question_popup_message(ins, title, message, yes_action, no_action):
        choice = QtWidgets.QMessageBox.question(ins, title, message,
                                             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            yes_action()
        else:
            no_action()
        return

    @staticmethod
    def create_alert_popup_message(ins, title, message):
        QtWidgets.QMessageBox.warning(ins, title, message)
        return

    @staticmethod
    def create_check_box(ins, size, obj_name, text, action):
        chk = QtWidgets.QCheckBox(ins)
        chk.setGeometry(size[0], size[1], size[2], size[3])
        chk.stateChanged.connect(action)
        chk.setText(text)
        chk.setObjectName(obj_name)
        return chk

    @staticmethod
    def create_progress_bar(ins, obj_name, auto_fill_bg=False, text_visible=False):
        prg = QtWidgets.QProgressBar(ins)
        prg.setAutoFillBackground(auto_fill_bg)
        prg.setTextVisible(text_visible)
        prg.setObjectName(obj_name)
        return prg

    @staticmethod
    def create_widget(ins, obj_name, size=None):
        wid = QtWidgets.QWidget(ins)
        wid.setObjectName(obj_name)
        if size:
            wid.setGeometry(size[0], size[1], size[2], size[3])
        return wid

    @staticmethod
    def create_box_layout(obj_name, axis, ins=None, margins=None):
        if axis == 0:
            if ins:
                bxl = QtWidgets.QHBoxLayout(ins)
            else:
                bxl = QtWidgets.QHBoxLayout()
        else:
            if ins:
                bxl = QtWidgets.QVBoxLayout(ins)
            else:
                bxl = QtWidgets.QVBoxLayout()

        bxl.setObjectName(obj_name)
        if margins:
            bxl.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
        return bxl

    @staticmethod
    def create_label(ins, obj_name, text):
        lbl = QtWidgets.QLabel(ins)
        lbl.setObjectName(obj_name)
        lbl.setText(text)
        return lbl

    @staticmethod
    def create_line_edit(ins, obj_name, placeholder_text, action=None):
        lne = QtWidgets.QLineEdit(ins)
        lne.setObjectName(obj_name)
        lne.setPlaceholderText(placeholder_text)
        if action:
            lne.editingFinished.connect(action)
        return lne

    @staticmethod
    def create_combo_box(ins, obj_name, items, action):
        cmb = QtWidgets.QComboBox(ins)
        cmb.setObjectName(obj_name)
        for i, item in enumerate(items):
            cmb.addItem(item)
            cmb.setItemText(i, item)
        cmb.currentTextChanged.connect(action)
        return cmb

    @staticmethod
    def create_statusbar(ins, obj_name):
        statusbar = QtWidgets.QStatusBar(ins)
        statusbar.setObjectName(obj_name)
        return statusbar

    @staticmethod
    def create_menubar(ins, obj_name, location):
        menubar = QtWidgets.QMenuBar(ins)
        menubar.setObjectName(obj_name)
        menubar.setGeometry(QtCore.QRect(location[0], location[1], location[2], location[3]))
        return menubar

    @staticmethod
    def create_menubar_entry(ins, obj_name, title):
        mne = QtWidgets.QMenu(ins)
        mne.setObjectName(obj_name)
        mne.setTitle(title)
        return mne

    @staticmethod
    def create_action(ins, obj_name, text, action, set_checkable=False):
        act = QtWidgets.QAction(ins)
        act.setObjectName(obj_name)
        act.triggered.connect(action)
        act.setCheckable(set_checkable)
        act.setText(text)
        return act

    @staticmethod
    def create_image_viewer(ins, obj_name, location, action):
        lbl = QImageViewer(ins, action)
        lbl.setObjectName(obj_name)
        lbl.setGeometry(QtCore.QRect(location[0], location[1], location[2], location[3]))
        return lbl


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.WidgetActions = WidgetActions(self)
        self.title = 'yt2mp3'
        self.icon = 'data/yt2mp3.png'
        self.app_id = 'Tymec.yt2mp3.main.0.5'
        self.init_ui()
        self.main_menu()

    def init_ui(self):
        self.setObjectName("window")
        self.setWindowTitle(self.title)
        self.setWindowIcon(QtGui.QIcon(self.icon))
        self.setGeometry(50, 50, 479, 241)
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.app_id)

    def main_menu(self):
        central_widget = CreateWidgets.create_widget(self, "centralwidget")

        # region BottomWidgets
        layout_widget = CreateWidgets.create_widget(central_widget, "layoutWidget", size=[10, 120, 461, 79])
        bottom_widgets = CreateWidgets.create_box_layout("bottomWidgets", 1, ins=layout_widget, margins=[0, 0, 0, 0])

        song_link_group = CreateWidgets.create_box_layout("songLinkGroup", 0)
        link_label_group = CreateWidgets.create_box_layout("linkLabelGroup", 1)

        youtube_link_label = CreateWidgets.create_label(layout_widget, "youtubeLinkLabel", "YouTube Link")
        link_label_group.addWidget(youtube_link_label)

        song_link_group.addLayout(link_label_group)
        link_input_group = CreateWidgets.create_box_layout("linkInputGroup", 1)

        youtube_link_input = CreateWidgets.create_line_edit(layout_widget, "youtubeLinkInput",
                                                            "Link to the YouTube song to download",
                                                            lambda: self.WidgetActions.set_youtube_link(
                                                                youtube_link_input.text()
                                                            ))
        link_input_group.addWidget(youtube_link_input)

        song_link_group.addLayout(link_input_group)
        bottom_widgets.addLayout(song_link_group)

        progress_bar = CreateWidgets.create_progress_bar(layout_widget, "progressBar")
        bottom_widgets.addWidget(progress_bar)
        # endregion
        # region TopWidgets
        layout_widget1 = CreateWidgets.create_widget(central_widget, "layoutWidget1", [140, 10, 331, 82])
        top_widgets = CreateWidgets.create_box_layout("topWidgets", 0, layout_widget1, [0, 0, 0, 0])
        # region SongTagWidgets
        song_tag_group = CreateWidgets.create_box_layout("songTagGroup", 0)
        tag_label_group = CreateWidgets.create_box_layout("tagLabelGroup", 1)

        # region Labels
        title_label = CreateWidgets.create_label(layout_widget1, "titleLabel", "Title")
        tag_label_group.addWidget(title_label)
        artist_label = CreateWidgets.create_label(layout_widget1, "artistLabel", "Artist")
        tag_label_group.addWidget(artist_label)
        album_label = CreateWidgets.create_label(layout_widget1, "albumLabel", "Album")
        tag_label_group.addWidget(album_label)
        # endregion

        song_tag_group.addLayout(tag_label_group)
        tag_input_group = CreateWidgets.create_box_layout("tagInputGroup", 1)

        # region Inputs
        title_input = CreateWidgets.create_line_edit(layout_widget1, "titleInput", "Title of the song",
                                                     lambda: self.WidgetActions.add_data("Title", title_input.text())
                                                     )
        tag_input_group.addWidget(title_input)
        artist_input = CreateWidgets.create_line_edit(layout_widget1, "artistInput", "Name of the artist",
                                                     lambda: self.WidgetActions.add_data("Artist", artist_input.text())
                                                     )
        tag_input_group.addWidget(artist_input)
        album_input = CreateWidgets.create_line_edit(layout_widget1, "albumInput", "Name of the album",
                                                     lambda: self.WidgetActions.add_data("Album", album_input.text())
                                                     )
        tag_input_group.addWidget(album_input)
        # endregion

        song_tag_group.addLayout(tag_input_group)
        top_widgets.addLayout(song_tag_group)
        # endregion
        # region ActionWidgets
        action_group = CreateWidgets.create_box_layout("actionGroup", 1)

        download_button = CreateWidgets.create_button(layout_widget1, "downloadButton", "Download",
                                                      self.WidgetActions.download
                                                      )
        action_group.addWidget(download_button)
        preview_song_button = CreateWidgets.create_button(layout_widget1, "previewSongButton", "Preview Song",
                                                          self.WidgetActions.preview_song
                                                          )
        action_group.addWidget(preview_song_button)
        preview_song_button.setDisabled(True)
        tag_fetch_combo = CreateWidgets.create_combo_box(layout_widget1, "tagFetchCombo",
                                                         ["Manual", "YouTube", "Spotify"],
                                                         self.WidgetActions.tag_fetch
                                                         )
        action_group.addWidget(tag_fetch_combo)
        tag_fetch_combo.setDisabled(True)

        top_widgets.addLayout(action_group)
        # endregion
        # endregion
        # region Bars
        statusbar = CreateWidgets.create_statusbar(self, "statusbar")

        menubar = CreateWidgets.create_menubar(self, "menubar", [0, 0, 479, 21])
        file_menu = CreateWidgets.create_menubar_entry(menubar, "menuFile", "&File")
        song_file_menu = CreateWidgets.create_menubar_entry(file_menu, "menuSong", "&New Song")

        action_single = CreateWidgets.create_action(self, "actionSingle", "Single",
                                                    lambda: self.WidgetActions.new_song(0)
                                                    )
        action_bulk = CreateWidgets.create_action(self, "actionBulk", "Bulk",
                                                  lambda: self.WidgetActions.new_song(1)
                                                  )
        action_exit = CreateWidgets.create_action(self, "actionExit", "&Exit", self.close)

        song_file_menu.addAction(action_single)
        song_file_menu.addAction(action_bulk)
        file_menu.addAction(song_file_menu.menuAction())
        file_menu.addAction(action_exit)

        options_menu = CreateWidgets.create_menubar_entry(menubar, "menuOptions", "&Options")
        action_instant_preview = CreateWidgets.create_action(self, "actionInstantPreview", "Instant Preview",
                                                             lambda: self.WidgetActions.add_data(
                                                                 'instantPreview',
                                                                 action_instant_preview.isChecked()
                                                             ), set_checkable=True
                                                             )
        action_instant_preview.setChecked(True)
        action_instant_play_preview = CreateWidgets.create_action(self, "actionInstantPlayPreview", "Instant Play Preview",
                                                             lambda: self.WidgetActions.add_data(
                                                                 'instantPlay',
                                                                 action_instant_play_preview.isChecked()
                                                             ), set_checkable=True
                                                             )
        action_instant_play_preview.setChecked(False)

        options_menu.addAction(action_instant_preview)
        options_menu.addAction(action_instant_play_preview)

        menubar.addAction(file_menu.menuAction())
        menubar.addAction(options_menu.menuAction())
        # endregion
        # region SeparateWidgets
        cover_art_preview = CreateWidgets.create_image_viewer(central_widget, "coverArtPreview", [10, 10, 121, 101],
                                                              self.WidgetActions.set_cover_art
                                                              )
        is_single = CreateWidgets.create_check_box(central_widget, [140, 90, 71, 31], "isSingle", "Is a single",
                                                   lambda: self.WidgetActions.is_single(is_single, album_input)
                                                   )
        # endregion
        # region SetWidgets
        self.setStatusBar(statusbar)
        self.setMenuBar(menubar)
        self.setCentralWidget(central_widget)
        QtCore.QMetaObject.connectSlotsByName(self)
        # endregion

        self.show()

    def closeEvent(self, event):
        CreateWidgets.create_question_popup_message(self, "Exit", "Are you sure?", event.accept, lambda: None)
        #os.remove('downloads/preview.wav')
        #os.remove('downloads/temp_cover.jpg')
        event.accept()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
