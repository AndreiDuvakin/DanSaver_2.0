import datetime
import os
import sys
import time
import threading

from PIL import Image
from PyQt5.QtCore import QTimer, QObject, QUrl, QSize
from PyQt5.QtGui import QIcon, QMovie, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from sqlalchemy.orm import Session
from uuid import uuid4

from data import types
from db_connect import init_data, create_session, Media, Extensions, Type, Categories, MediaCetegories

from PyQt5 import uic, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QPushButton, QListWidgetItem, \
    QListWidget, QDialog, QLabel, QWidget, QTabWidget, QTextBrowser, QLineEdit


class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('win/MainWin.ui', self)
        self.ui_init()

    def ui_init(self):
        self.pushButton.clicked.connect(self.add_files)
        self.pushButton_2.clicked.connect(self.outload_files)
        self.pushButton_3.clicked.connect(self.manage_files)

    def add_files(self):
        path = QFileDialog.getExistingDirectory(self, "Выбрать папку", ".")
        if path:
            resp = list(
                filter(lambda x: x is not None, map(lambda x: self.check_file(path + '/' + x), os.listdir(path))))
            self.ms = QMessageBox()
            self.ms.setWindowTitle("Файлы загружены")
            self.ms.setText(
                f'Объектов обработано: {str(len(os.listdir(path)))}, новых объектов добавлено: {str(len(resp))}')
            self.ms.show()

    def check_file(self, path):
        with open(path, 'rb') as file:
            data = file.read()
            session = create_session()
            if not session.query(Media).filter(Media.data == data).first():
                exe = session.query(Extensions).filter(Extensions.name == path.split('.')[-1]).first()
                if not exe:
                    check_exe = session.query(Extensions).order_by(-Extensions.id).first()
                    if check_exe:
                        exe = Extensions(
                            id=check_exe.id + 1,
                            name=path.split('/')[-1].split('.')[1].lower(),
                        )
                    else:
                        exe = Extensions(
                            id=1,
                            name=path.split('/')[-1].split('.')[1].lower(),
                        )
                    try:
                        tpe = session.query(Type.id).filter(
                            Type.name == types[path.split('/')[-1].split('.')[1]]).first()
                        exe.type_id = tpe.id
                    except KeyError:
                        pass
                    session.add(exe)
                    session.commit()
                new_media = Media(
                    name=path.split('/')[-1].split('.')[0],
                    data=data,
                    exe_id=exe.id
                )
                session.add(new_media)
                session.commit()
                session.close()
                return path
            session.close()

    def outload_files(self):
        path = QFileDialog.getExistingDirectory(self, "Выбрать папку", ".")
        session = create_session()
        all_media = session.query(Media).all()
        for i in all_media:
            with open(path + '/' + i.name + '.' + session.query(Extensions).filter(
                    Extensions.id == i.exe_id).first().name, 'wb') as file:
                file.write(i.data)
        session.close()
        self.ms = QMessageBox()
        self.ms.setWindowTitle("Файлы выгружены")
        self.ms.setText(f"Объектов выгружено: {str(len(all_media))}")
        self.ms.show()

    def manage_files(self):
        self.manage = ManageMediaWin()
        self.manage.show()


class MediaItemWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('win/MediaItemWidget.ui', self)


class ManageMediaWin(QMainWindow):
    started_data = QtCore.pyqtSignal()
    finished_data = QtCore.pyqtSignal()
    work_end = QtCore.pyqtSignal()
    icon_make = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.all_wids = None
        self.data = None
        uic.loadUi('win/ManageFilesWin.ui', self)
        self.finished_data.connect(self.make_wid)
        self.ms = QMessageBox()
        self.ms.setWindowTitle('Загрузка')
        self.ms.setText('Загрузка данных, пожалуйста подождите')
        self.ms.show()
        self.start()
        self.work_end.connect(self.make_items)
        self.open_mode = False
        self.tabWidget.setVisible(False)
        self.last_sender = None
        self.item_dict = {}
        pixmap = QPixmap('img/main/heart.png').scaled(30, 30)
        cursor = QtGui.QCursor(pixmap)
        self.pushButton.setCursor(cursor)
        self.pushButton.clicked.connect(self.open_win_media)
        self.pushButton_3.setVisible(False)
        self.pushButton_2.clicked.connect(self.export)
        self.lineEdit_2.textChanged.connect(self.check_name)
        self.pushButton_3.clicked.connect(self.rename)

    def rename(self):
        session = create_session()
        all_names = list(map(lambda x: x[0].lower(), session.query(Media.name).all()))
        if self.lineEdit_2.text().lower() in all_names:
            self.ms = QMessageBox()
            self.ms.setWindowTitle('Уже существует')
            self.ms.setText('Файл с таким именем уже существует')
            self.ms.show()
        else:
            current_media = session.query(Media).filter(Media.id == self.item_dict[self.last_sender][0].id).first()
            if current_media:
                current_media.name = self.lineEdit_2.text()
                session.commit()
                self.pushButton_3.setVisible(False)
                self.item_dict[self.last_sender][0].name = self.lineEdit_2.text()
                self.item_dict[self.last_sender][1].textBrowser.setPlainText(
                    f'{self.lineEdit_2.text()}.{self.label_7.text()}')
        session.close()

    def check_name(self):
        if self.lineEdit_2.text().lower() != self.item_dict[self.last_sender][0].name.lower():
            self.pushButton_3.setVisible(True)
        else:
            self.pushButton_3.setVisible(False)

    def export(self):
        path = QFileDialog.getExistingDirectory(self, "Выбрать папку", ".")
        if path:
            with open(f'{path}/{self.item_dict[self.last_sender][0].name}.{self.label_7.text()}', 'wb') as file:
                file.write(self.item_dict[self.last_sender][0].data)

    def open_win_media(self):
        self.viewer = MediaViewer(self.item_dict[self.last_sender])
        self.viewer.show()

    def make_wid(self):
        self.all_wids = list(map(lambda x: self.set_data_wid(x), self.data))
        self.work_end.emit()

    def make_icons(self):
        self.lineEdit.setEnabled(False)
        list(map(lambda x: threading.Thread(target=self.set_icon,
                                            args=[x, f'img/icon_data/{x.textBrowser.toPlainText()}'],
                                            daemon=True).start(), self.all_wids))
        self.lineEdit.setEnabled(True)
        self.icon_make.emit()

    def set_data_wid(self, data):
        wid = MediaItemWidget()
        wid.textBrowser.setPlainText(data[1].split('/')[-1])
        self.item_dict[wid.pushButton_2] = [data[0], wid]
        wid.pushButton_2.clicked.connect(self.click_media)
        match types[data[1].split('/')[-1].split('.')[-1]]:
            case 'photo':
                pass
            case _:
                wid.pushButton.setVisible(False)
        return wid

    @staticmethod
    def set_icon(wid: MediaItemWidget, img: str):
        wid.pushButton.setIcon(QIcon(img))

    def start(self):
        self.started_data.emit()
        session = create_session()
        all_media = session.query(Media).all()
        all_exe = session.query(Extensions).all()
        session.close()
        threading.Thread(target=self.get_data, args=[all_media, all_exe], daemon=True).start()

    def get_data(self, all_media, all_exe):
        names = list(map(lambda x: self.make_media_item(x, all_exe), all_media))
        self.data = list(map(lambda x: [all_media[x], names[x]], range(len(all_media))))
        self.finished_data.emit()

    @staticmethod
    def make_media_item(media, all_exe) -> str:
        name = None
        exe = list(filter(lambda x: x.id == media.exe_id, all_exe))
        if exe:
            name = 'img/icon_data/' + media.name + '.' + exe[0].name
            with open(name, 'wb') as file:
                file.write(media.data)
        return name

    def make_items(self):
        wid_data = self.all_wids
        self.listWidget.setIconSize(QtCore.QSize(200, 200))
        list(map(lambda x: self.add_item(x), wid_data))
        threading.Thread(target=self.make_icons, daemon=True).start()
        self.ms.close()

    def rm_media(self):
        list(map(lambda x: os.remove(f'img/icon_data/{x}'), os.listdir('img/icon_data')))

    def add_item(self, wid):
        item = QListWidgetItem()
        self.listWidget.addItem(item)
        self.listWidget.setItemWidget(item, wid)

    def click_media(self):
        match self.sender():
            case self.last_sender:
                self.last_sender = None
                self.open_mode = False
                self.tabWidget.setVisible(self.open_mode)
                self.sender().setText('Открыть')
            case _:
                self.sender().setText('Закрыть')
                if self.last_sender:
                    if self.last_sender.text() == 'Закрыть':
                        self.last_sender.setText('Открыть')
                self.last_sender = self.sender()
                self.open_mode = True
                self.tabWidget.setVisible(self.open_mode)
                self.open_media()

    def open_media(self):
        data = self.item_dict[self.sender()]
        path = data[1].textBrowser.toPlainText()
        self.label_4.setText(data[0].date.strftime('%H:%M %d.%m.%Y'))
        self.label_7.setText(path.split('.')[-1])
        self.label_6.setText(types[path.split('.')[-1]].capitalize())
        self.lineEdit_2.setText(self.item_dict[self.last_sender][0].name)
        match types[path.split('.')[-1]]:
            case 'photo':
                self.pushButton.setIcon(QIcon(f'img/icon_data/{path}'))
            case _:
                pass


class MediaViewer(QMainWindow):
    def __init__(self, media):
        super().__init__()
        uic.loadUi('win/PhotoViewer.ui', self)
        session = create_session()
        exe = session.query(Extensions).filter(Extensions.id == media[0].exe_id).first().name
        session.close()
        self.path = f'img/icon_data/{media[0].name}.{exe}'
        self.label.setPixmap(QPixmap(self.path))
        self.setWindowTitle(f'Просмотр {media[0].name}.{exe}')
        im = Image.open(self.path)
        width, height = im.size
        self.relationship = height / width
        self.setMaximumSize(QSize(round(800 / self.relationship), 600))
        self.label.setMaximumSize(QSize(round(900 / self.relationship), 900))
        pixmap = QPixmap('img/main/heart.png').scaled(40, 40)
        cursor = QtGui.QCursor(pixmap)
        self.setCursor(cursor)


class LoaderWin(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('win/LoadingWin.ui', self)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.movie = QMovie('img/loading.gif')
        self.label.setMovie(self.movie)
        self.movie.start()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    init_data()
    list(map(lambda x: os.remove(f'img/icon_data/{x}'), os.listdir('img/icon_data')))
    app = QApplication(sys.argv)
    win = MainWin()
    win.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
