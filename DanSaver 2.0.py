import os
import sys

from data import types
from db_connect import init_data, create_session, Media, Extensions, Type, Categories, MediaCetegories

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox


class LoginWin(QMainWindow):
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


class ManageMediaWin(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('win/ManageFilesWin.ui', self)
        self.init_data()

    def init_data(self):
        session = create_session()
        all_media = session.query(Media).all()

    def make_media_button(self):
        pass


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    init_data()
    app = QApplication(sys.argv)
    win = LoginWin()
    win.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
