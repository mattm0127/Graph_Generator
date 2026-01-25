from PySide6.QtWidgets import (QWidget,
                               QPushButton,
                               QLabel,
                               QGridLayout,
                               QFileDialog)
from PySide6.QtCore import (Qt, 
                            QThread, 
                            QObject,
                            QUrl, 
                            Signal, 
                            Slot)
from PySide6.QtWebEngineWidgets import QWebEngineView
import pandas as pd
import plotly.express as px
import os

class ChartWorker(QObject):

    file_loaded = Signal(str)
    result_ready = Signal(str)

    def __init__(self):
        super().__init__()
        self.df : pd.DataFrame = None
    
    @Slot(str)
    def load_file(self, path):
        self.df = pd.read_excel(path)

    @Slot()
    def generate_graph(self):
        temp_file = os.path.abspath("temp_chart.html")
        
        fig = px.scatter(self.df, x='Date', y='Value')
        fig.write_html(temp_file, include_plotlyjs=True)
        self.result_ready.emit(temp_file)

class GraphWindow(QWidget):

    upload_file = Signal(str)
    request_graph = Signal(str)

    def __init__(self):

        super().__init__()

        self.grid_layout = QGridLayout(self)
        for col in range(5):
            self.grid_layout.setColumnStretch(col, 1)
        for row in range(5):
            self.grid_layout.setRowStretch(row, 1)
        
        self.web = QWebEngineView(self)
        self.web.setHtml('<h1> Waiting for Data...</h1>')
        self.grid_layout.addWidget(self.web, 1, 0, 4, 5)

        self.input_file = ""

        self._add_labels()
        self._add_buttons()

        self.start_worker()

    def start_worker(self):
        self.chart_thread = QThread()
        self.worker = ChartWorker()
        self.worker.moveToThread(self.chart_thread)

        self.request_graph.connect(self.worker.generate_graph)
        self.worker.result_ready.connect(self.show_graph)

        self.chart_thread.start()

    @Slot()
    def start(self):
        self.request_graph.emit(self.input_file)

    @Slot(str)
    def show_graph(self, temp_file):
        file = QUrl.fromLocalFile(temp_file)
        self.web.load(file)

    @Slot()
    def _input_dialog(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Excel File...",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if filename:
            self.input_file = filename
            self.input_file_label.setText(self.input_file)

    def _add_labels(self):

        self.title_label = QLabel("Lets Generate!")
        self.title_label.setStyleSheet("font-weight: bold;")

        self.input_file_label = QLabel("Choose a file...", self)

        self.grid_layout.addWidget(self.title_label, 0, 0, 1, 4, Qt.AlignmentFlag.AlignCenter)
        self.grid_layout.addWidget(self.input_file_label, 0, 4, Qt.AlignmentFlag.AlignTop)

    def _add_buttons(self):

        self.file_button = QPushButton("Select Excel File", self)
        self.file_button.setFixedHeight(35)
        self.file_button.clicked.connect(self._input_dialog)
        self.start_button = QPushButton("Show Graph")
        self.start_button.clicked.connect(self.start)

        self.grid_layout.addWidget(self.file_button, 0, 4, Qt.AlignmentFlag.AlignCenter)
        self.grid_layout.addWidget(self.start_button, 0, 4, Qt.AlignmentFlag.AlignBottom)
 
    def cleanup(self):
        if self.chart_thread.isRunning():
            self.chart_thread.quit()
            self.chart_thread.wait()

        




        
