import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow


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
        pass

    def outload_files(self):
        pass

    def manage_files(self):
        pass


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = LoginWin()
    win.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
