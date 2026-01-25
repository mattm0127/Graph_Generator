from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget
)
from PySide6.QtGui import (
    QIcon
)
import sys
import os

from windows import GraphWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Data Visualizer")
        self.setMinimumWidth(1280)
        self.setMinimumHeight(720)

        self.icon = QIcon()
        self.icon.addFile(os.path.abspath('app_icon.png'))
        self.setWindowIcon(self.icon)

        self.window_stack = QStackedWidget()
        self.setCentralWidget(self.window_stack)

        # Dictionary of all windows, key is position in Widget Stack
        self.window_dict = {
            0: GraphWindow(),
        }
       
        for x in range(len(self.window_dict)):
            if self.window_stack.find(x):
                self.window_stack.removeWidget(self.window_stack.find(x))
            self.window_stack.insertWidget(x, self.window_dict[x])
    
    def closeEvent(self, event):
        self.window_dict[0].cleanup()
        return super().closeEvent(event)

def run_program():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_program()