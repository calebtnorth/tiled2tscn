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

if __name__ == "__main__":
    app = Application(sys.argv)
    MainWindow()
    mw.show()
    app.exec()