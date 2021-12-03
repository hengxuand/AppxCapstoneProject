import sys
import VTKrenderwindow
import os

from PyQt5.QtWidgets import (QApplication, QMainWindow)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.w = None
        self.curdir = os.path.dirname(__file__)
        self.ct_path = os.path.join(self.curdir, 'data/volume-105.nhdr')
        self.stl_path = os.path.join(self.curdir, 'data/Liver.stl')
        self.title = "VTK Render Window"
        self.setStyleSheet("QMainWindow {background: 'yellow';}")
        self.window2(self.ct_path, self.stl_path)

    def window2(self, ct_file, stl_file):
        print("window2" + ct_file + stl_file)

        self.w = VTKrenderwindow.RenderWindow(ct_file, stl_file)
        self.w.showFullScreen()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec())
