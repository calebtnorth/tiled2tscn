# tiled2hva
# UI to convert Tiled .tmx files to Godot .tscn for High Velocity Arena 

# Copyright (c) 2023 Caleb North

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sellcccccc
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
sys.dont_write_bytecode = True

from converter import Convert, ConversionError

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *



###########
### APP ###
###########
class Application(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationDisplayName("tiled2hva")

###################
### MAIN WINDOW ###
###################
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("tiled2hva")
        self.setMinimumWidth(300)

        # MAIN WINDOW
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)


        # BUTTONS
        buttons = QWidget()
        buttons_layout = QVBoxLayout()
        buttons.setLayout(buttons_layout)
        main_layout.addWidget(buttons)

        select_file_button = QPushButton(text="Select file")
        select_file_button.clicked.connect(self.select_file)
        select_file_button.setFixedWidth(100)
        buttons_layout.addWidget(select_file_button)

        self.generate_button = QPushButton(text="Generate")
        self.generate_button.clicked.connect(self.generate_file)
        self.generate_button.setDisabled(True)
        self.generate_button.setFixedWidth(100)
        buttons_layout.addWidget(self.generate_button)

        # INFORMATION BOX
        info_box = QGroupBox()
        info_box_layout = QVBoxLayout()
        info_box.setLayout(info_box_layout)
        main_layout.addWidget(info_box)

        self.tilemap_name = QLabel("")
        info_box_layout.addWidget(self.tilemap_name)

        self.tilemap_mode = QLabel("")
        info_box_layout.addWidget(self.tilemap_mode)

        self.tilemap_tile_size = QLabel("")
        info_box_layout.addWidget(self.tilemap_tile_size)

        self.tilemap_layers = QLabel("")
        info_box_layout.addWidget(self.tilemap_layers)

        self.tilemap_objects = QLabel("")
        info_box_layout.addWidget(self.tilemap_objects)

        # STATUS BAR
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("No file selected")
        self.selected_file_path = ""

        self.show()

    def select_file(self):
        selected_file_path:str = QFileDialog.getOpenFileName(self, "Open File", "C:\\", "Tilemap files (*.tmx)")[0]
        if not selected_file_path:
            if not self.selected_file_path:
                self.generate_button.setDisabled(True)
                return
            self.generate_button.setDisabled(False)
            return

        self.selected_file_path = selected_file_path
        self.status_bar.showMessage(self.selected_file_path)
        self.generate_button.setDisabled(False)

    def generate_file(self):
        converter = Convert(self.selected_file_path)
        self.tilemap_name.setText(f"Name: {converter.name}")
        self.tilemap_mode.setText(f"Mode: {converter.mode}")

###########
### RUN ###
###########
if __name__ == "__main__":
    app = Application(sys.argv)
    main_window = MainWindow()
    app.exec()