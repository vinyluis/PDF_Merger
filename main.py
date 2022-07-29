"""
Main code for the PDF Merger with a simple PyQT-based GUI
"""

# ---- IMPORTS ----

import os
import sys
from time import sleep
from PyPDF2 import PdfMerger

# Window building
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtCore import QObject, QThread, pyqtSignal

# Import the layout
from layouts.layout import Ui_MainWindow

# Software version
v = "v1.0.1"

# ---- FUNCTIONS ----


def message_box(type, msg):
    # Type assessment
    if type == "error":
        title = "Error!"
    elif type == "info":
        title = "PDF Merger"
    else:
        raise ValueError(f"Type undefined for message box. Received {type}")
    # Creates and displays the message box
    msgbox = QMessageBox()
    msgbox.setWindowTitle(title)
    msgbox.setText(msg)
    msgbox.exec_()
    return -1


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# ---- CLASSES ----


class MainWindow(Ui_MainWindow):

    """
    Main window class. Allows to manipulate window objects.
    """

    def __init__(self):
        """
        Inherits from Ui_MainWindow and creates the Merger object.
        """
        super(MainWindow, self).__init__()
        self.merger = Merger()

    def setupUi(self, Window):
        """
        Setup method to make the first adjustments to the screen.
        Inherits also from parent, then runs extra instructions.
        """
        super(MainWindow, self).setupUi(Window)
        # ---- Adds new instructions ----
        # Defines logo and icon paths
        self.img_file1.setPixmap(QtGui.QPixmap(img_notloaded_path))
        self.img_file2.setPixmap(QtGui.QPixmap(img_notloaded_path))
        Window.setWindowIcon(QtGui.QIcon(icon_path))
        # Shows the SW version on the status bar
        self.set_status(v)
        # Sets up the signal connections
        self.setup_connections()
        # Makes sure that the window will not be resized
        Window.setFixedSize(380, 330)
        # Removes placeholder text from the labels
        self.lbl_file1.setText("")
        self.lbl_file2.setText("")

    def set_status(self, text):
        """
        Changes the statusbar text
        """
        self.statusbar.showMessage(text)

    def setup_connections(self):
        """
        Build the connections
        """
        self.but_file1.clicked.connect(lambda: self.run_off_thread(lambda: self.merger.load_file(1, self.lbl_file1, self.img_file1)))
        self.but_file2.clicked.connect(lambda: self.run_off_thread(lambda: self.merger.load_file(2, self.lbl_file2, self.img_file2)))
        self.but_merge.clicked.connect(lambda: self.run_off_thread(lambda: self.merger.merge_files()))

    def enable_all_buttons(self, state):
        """
        Enables (state = True) or disables (state = False) all buttons on the screen
        """
        self.but_file1.setEnabled(state)
        self.but_file2.setEnabled(state)
        self.but_merge.setEnabled(state)

    def run_off_thread(self, function):
        """
        Runs functions which are fast enough to run on the main thread,
        or to run functions that are heavily dependent of the GUI
        """
        # Disables all buttons
        self.enable_all_buttons(False)
        # Runs the function
        function()
        # Enables all buttons
        self.enable_all_buttons(True)

    def run_on_thread(self, function):
        """
        Runs functions in another thread, preventing screen freezes.
        Allows for one function at a time and disables all other buttons to prevent new threads.
        """
        # Creates the thread
        self.thread = QThread()
        # Creates a worker for the given function
        self.worker = Worker(function)
        # Moves the worker to the thread
        self.worker.moveToThread(self.thread)

        # Connects signals and slots
        self.thread.started.connect(self.worker.run)  # Runs the worker
        self.worker.finished.connect(self.thread.quit)  # Quits the thread when the worker is done
        self.worker.finished.connect(self.worker.deleteLater)  # Deletes the worker when it is done
        self.thread.finished.connect(lambda: self.enable_all_buttons(True))  # Enables all buttons as soon as the thread is finished
        self.thread.finished.connect(self.thread.deleteLater)  # Deletes the thread when it is finished

        # Disables all buttons to prevent new threads
        self.enable_all_buttons(False)

        # Starts the thread
        self.thread.start()

        # Avoids error "QPainter::setCompositionMode: Painter not active"
        sleep(1)


class Worker(QObject):
    """
    Generic woker for using threading. Runs the function passed on initialization.
    """
    finished = pyqtSignal()

    def __init__(self, function):
        super(Worker, self).__init__()
        self.function = function

    def run(self):
        self.function()
        self.finished.emit()


class Merger():
    """
    Class responsible of gathering the PDF files, merging them and saving the result.
    """

    def __init__(self):
        self.files = {}

    def load_file(self, num_file, label, img):
        """
        Loads the file defined by num_file and updates the label
        """
        # Verify if num_file is correct
        if (num_file != 1) and (num_file != 2):
            raise ValueError("Error defining file number")
        # Choose the file
        file = self.open_file_dialog()
        # Store it in an attribute and update the label
        if (file is not None) and (file != ""):
            # Stores
            self.files[num_file] = file
            # Clip the text to 27 characters
            if len(file) > 27:
                # filepath = file[-26:]
                # filepath = '...' + file[-23:]
                filepath = file[:6] + '...' + file[-15:]
            else:
                filepath = file
            # Update the label accordingly
            label.setText(filepath)
            # Updates the icon
            img.setPixmap(QtGui.QPixmap(img_loaded_path))

    def merge_files(self):
        """
        Merges the two selected files
        """
        # Build the merger object
        merger = PdfMerger()
        # Assert if all files have been selected
        if len(self.files) == 0:
            message_box('error', "No files were selected")
            return -1
        elif len(self.files) == 1:
            message_box('error', "Only one file was selected")
            return -1
        # Merge the files
        for key, file in self.files.items():
            if file is None:
                message_box('error', f"File {key} not found")
                return -1
            merger.append(file)
        # Choose the save path
        file = self.save_file_dialog()
        print(file)
        # Write the result
        if file is not None:
            merger.write(file)
            merger.close()
            message_box('info', f"File sucessfully saved on \n {file}")

    @staticmethod
    def open_file_dialog():
        """
        Shows an Open File dialog window and returns the filepath
        """
        # Shows the dialog
        message = "Open PDF file"
        file, _ = QFileDialog.getOpenFileName(caption=message, filter="PDF files (*.pdf);;All files (*.*)")
        # Returns the filepath
        return file

    @staticmethod
    def save_file_dialog(dummy_filename="Result.pdf"):
        """
        Shows a Save File dialog window and returns the filepath
        """
        # Shows the dialog
        message = "Save PDF file"
        file, _ = QFileDialog.getSaveFileName(caption=message, directory=dummy_filename, filter="PDF files (*.pdf);;All files (*.*)")
        # Returns the filepath
        return file


# ---- MAIN ----


if __name__ == "__main__":

    # Path to the images
    img_loaded_path = resource_path("images/icon_loaded.png")
    img_notloaded_path = resource_path("images/icon_notloaded.png")
    icon_path = resource_path("images/icon.ico")

    print(img_notloaded_path)

    print("Starting program....")
    app = QApplication(sys.argv)
    window = QMainWindow()
    ui = MainWindow()
    ui.setupUi(window)
    print("Program started\n")
    window.show()
    sys.exit(app.exec_())
