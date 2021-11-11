import sys
import VTKrenderwindow
import vtk
from PyQt5 import QtCore, QtGui
from PyQt5 import Qt
import os

from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton,
                             QToolTip, QMessageBox, QLabel, QFileDialog)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.w = None
        self.curdir = os.path.dirname(__file__)
        self.ct_path = os.path.join(self.curdir, '../data/volume-105.nhdr')
        self.stl_path = os.path.join(self.curdir, '../data/Liver.stl')
        self.title = "VTK Render Window"

        # self.BrowseButton_ct = QPushButton("Browse CT File", self)
        # self.BrowseButton_ct.move(200, 175)
        # self.BrowseButton_ct.setToolTip(
        #     "<h4>Browse file you want to up load</h4>")
        # self.BrowseButton_ct.clicked.connect(self.ct_browseButton_handler)
        #
        # self.BrowseButton_stl = QPushButton("Browse stl File", self)
        # self.BrowseButton_stl.move(350, 175)
        # self.BrowseButton_stl.setToolTip(
        #     "<h4>Browse file you want to up load</h4>")
        # self.BrowseButton_stl.clicked.connect(self.stl_browseButton_handler)
        #
        # self.pushButton = QPushButton("Upload", self)
        # self.pushButton.move(275, 250)
        # self.pushButton.setToolTip("<h3>Start the Session</h3>")
        #
        # self.pushButton.clicked.connect(self.window2_button_handler)

        self.window2(self.ct_path, self.stl_path)
        # self.main_window()

    # def main_window(self):
    #     # self.label = QLabel("Here is file direction", self)
    #     # self.label.move(285, 175)
    #     self.setWindowTitle(self.title)
    #     self.setGeometry(self.top, self.left, self.width, self.height)
    #     self.show()

    def window2(self, ct_file, stl_file):
        print("window2" + ct_file + stl_file)
        self.w = VTKrenderwindow.RenderWindow(ct_file, stl_file)
        # self.w.showMaximized()
        self.w.showFullScreen()
        # self.hide()

    # def window2_button_handler(self):
    #     if len(self.ct_path) != 0 and len(self.stl_path) != 0:
    #         print("handler" + self.ct_path + self.stl_path)
    #         self.window2(self.ct_path, self.stl_path)
    #
    # def ct_browseButton_handler(self):
    #     print("Browse Button pressed")
    #     self.open_dialog_box(1)
    #
    # def stl_browseButton_handler(self):
    #     print("Browse Button pressed")
    #     self.open_dialog_box(2)

    # def open_dialog_box(self, flag):
    #     filename = QFileDialog.getOpenFileName()
    #     if flag == 1:
    #         self.ct_path = filename[0]
    #     elif flag == 2:
    #         self.stl_path = filename[0]
    #     print(filename)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec())
