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

from converter import Convert, Tilemap, ConversionError
from pickle import dumps, loads
from os import getenv, mkdir, listdir, remove
from os.path import join, normpath, split
from shutil import copyfile

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
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)

        # TOOLBAR
        self.config_path = normpath(join(getenv("APPDATA"), "tiled2hva/config"))
        self.menu = self.menuBar()

        # File Menu
        self.file_menu = self.menu.addMenu("&File")

        self.save_maps_list = QAction("&Save maps list", self)
        self.save_maps_list.setStatusTip("Save the list of maps")
        self.save_maps_list.triggered.connect(self.save_maps_list_items)
        self.file_menu.addAction(self.save_maps_list)

        self.load_maps_list = QAction("&Load maps list", self)
        self.load_maps_list.setStatusTip("Load the list of maps")
        self.load_maps_list.triggered.connect(self.load_maps_list_items)
        self.file_menu.addAction(self.load_maps_list)

        self.file_menu.addSeparator()

        self.save_destination_list = QAction("S&ave destination list", self)
        self.save_destination_list.setStatusTip("Save the list of maps")
        self.save_destination_list.triggered.connect(self.save_destination_list_items)
        self.file_menu.addAction(self.save_destination_list)

        self.load_destination_list = QAction("L&oad destination list", self)
        self.load_destination_list.setStatusTip("Save the list of maps")
        self.load_destination_list.triggered.connect(self.load_destination_list_items)
        self.file_menu.addAction(self.load_destination_list)
        # self.load_maps_list
        # self.save_destination_list
        # self.load_destination_list
        
        self.maps_menu = self.menu.addMenu("&Maps")

        self.destinations_menu = self.menu.addMenu("&Destinations")

        # MAP SELECTION
        self.selection_box = QGroupBox()
        self.selection_box_layout = QGridLayout()
        self.selection_box.setLayout(self.selection_box_layout)
        self.main_layout.addWidget(self.selection_box)
        
        self.map_list = QListWidget()
        self.selection_box_layout.addWidget(self.map_list, 0, 0, 1, 2)

        self.add_map = QPushButton("Add map")
        self.add_map.clicked.connect(self.select_map_item)
        self.selection_box_layout.addWidget(self.add_map, 1, 0)
        
        self.remove_map = QPushButton("Remove map")
        self.remove_map.clicked.connect(self.remove_map_item)
        self.selection_box_layout.addWidget(self.remove_map, 1, 1)

        # OPTIONS
        self.options = QWidget()
        self.options_layout = QVBoxLayout()
        self.options_layout.setAlignment(Qt.AlignTop)
        self.options.setLayout(self.options_layout)
        self.main_layout.addWidget(self.options)

        self.convert = QPushButton("Convert")
        self.convert.clicked.connect(self.convert_maps)
        self.options_layout.addWidget(self.convert)

        self.nest = QCheckBox("Nest")
        self.options_layout.addWidget(self.nest)

        # DESTINATIONS
        self.destination_box = QGroupBox()
        self.destination_box_layout = QGridLayout()
        self.destination_box.setLayout(self.destination_box_layout)
        self.main_layout.addWidget(self.destination_box)
        
        self.destination_list = QListWidget()
        self.destination_box_layout.addWidget(self.destination_list, 0, 0, 1, 2)

        self.add_destination = QPushButton("Add destination")
        self.add_destination.clicked.connect(self.select_destination_item)
        self.destination_box_layout.addWidget(self.add_destination, 1, 0)
        
        self.remove_destination = QPushButton("Remove destination")
        self.remove_destination.clicked.connect(self.remove_destination_item)
        self.destination_box_layout.addWidget(self.remove_destination, 1, 1)

        self.show()

    def select_map_item(self):
        selected_file_path:str = QFileDialog.getOpenFileName(self, "Open File", "C:\\", "Tilemap files (*.tmx)")[0]
        if selected_file_path:
            self.map_list.addItem(selected_file_path)

    def remove_map_item(self):
        self.map_list.takeItem(self.map_list.currentRow())

    def select_destination_item(self):
        selected_folder_path:str = QFileDialog.getExistingDirectory()
        if selected_folder_path:
            self.destination_list.addItem(selected_folder_path)

    def remove_destination_item(self):
        self.destination_list.takeItem(self.destination_list.currentRow())

    def convert_maps(self):
        # Check map list
        if self.map_list.count() < 1:
            QMessageBox.warning(
                self,
                "Missing maps",
                "Please add a valid .tmx to the map list",
                buttons=QMessageBox.Ok
            )
            return

        # Check destination list
        if self.destination_list.count() < 1:
            QMessageBox.warning(
                self,
                "Missing destinations",
                "Please add a valid destination folder",
                buttons=QMessageBox.Ok
            )
            return

        for map_id in range(0, self.map_list.count()):
            for destination_id in range(0, self.destination_list.count()):
                map = self.map_list.item(map_id).text()
                destination = self.destination_list.item(destination_id).text()

                tilemap = Tilemap(map)
                convert = Convert(tilemap)
                map_name = f"{tilemap.mode}_{tilemap.name}"
                full_destination = normpath(join(destination, f"{map_name}/"))

                try:
                    mkdir(full_destination)
                except Exception as e:
                    for file in listdir(full_destination):
                        remove(join(full_destination, file))


                with open(join(full_destination, f"{map_name}.tres"), "w+") as file:
                    file.write(convert.tres)

                with open(join(full_destination, f"{map_name}.tscn"), "w+") as file:
                    file.write(convert.tscn)

                for image in convert.images:
                    origin = join(split(map)[0], image)
                    destination = join(join(destination, f"{map_name}"), image)
                    copyfile(origin, destination)

    # Saving, loading
    def save_maps_list_items(self):
        try:
            config = [[], self.load_list_items(1)]
        except Exception as e:
            config = [[], []]

        for item in range(0, self.map_list.count()):
            config[0].append(self.map_list.item(item).text())

        with open(self.config_path, "w") as file:
            file.write(dumps(config))

    def load_maps_list_items(self):
        config = self.load_list_items(0)
        self.map_list.clear()
        for item in config:
            self.map_list.addItem(item)

    def save_destination_list_items(self):
        try:
            config = [self.load_list_items(0), []]
        except Exception as e:
            config = [[], []]

        for item in range(0, self.destination_list.count()):
            config[1].append(self.destination_list.item(item).text())

        with open(self.config_path, "w") as file:
            file.write(dumps(config))

    def load_destination_list_items(self):
        config = self.load_list_items(0)
        self.map_list.clear()
        for item in config:
            self.map_list.addItem(item)        

    def load_list_items(self, i):
        config = []
        with open(self.config_path, "r+") as file:
            file_contents = file.read()
            if file_contents != "":
                config = loads(file_contents)[i]

        return config
            

###########
### RUN ###
###########
if __name__ == "__main__":
    app = Application(sys.argv)
    main_window = MainWindow()
    app.exec()