from PySide6.QtWidgets import (QWidget,
                               QPushButton,
                               QLabel,
                               QGridLayout,
                               QFileDialog,
                               QComboBox,
                               QSizePolicy)
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

    file_loaded = Signal(list)
    result_ready = Signal(str)

    def __init__(self):
        super().__init__()
        self.df : pd.DataFrame = None
    
    @Slot(str)
    def load_file(self, path):
        self.df = pd.read_excel(path)
        filter_data = self.df.columns
        self.file_loaded.emit(filter_data)

    @Slot(list)
    def generate_graph(self, filters):

        temp_file = os.path.abspath("temp_graph.html")
        x_data, y_data, data_filter = filters
        if data_filter:
            fig = px.scatter(self.df, x=x_data, y=y_data, color=data_filter, title=y_data)
            fig.update_layout(showlegend=True)
        else:
            fig = px.scatter(self.df, x=x_data, y=y_data, title=y_data)
        fig.write_html(temp_file, include_plotlyjs=True)

        self.result_ready.emit(temp_file)


class GraphWindow(QWidget):

    upload_file = Signal(str)
    request_graph = Signal(list)

    def __init__(self):

        super().__init__()

        self.grid_layout = QGridLayout(self)
        for col in range(5):
            self.grid_layout.setColumnStretch(col, 1)
        for row in range(5):
            if row == 0:
                self.grid_layout.setRowMinimumHeight(row, 50)
                continue
            self.grid_layout.setRowStretch(row, 1)
        
        self.web = QWebEngineView(self)
        self.web.setHtml('<h1 style="text-align: right">&#8593 Select a File</h1>')
        self.grid_layout.addWidget(self.web, 1, 0, 4, 5)

        self._add_labels()
        self._add_buttons()

        self._start_worker()

    # Private Functions

    def _start_worker(self):
        self.chart_thread = QThread()
        self.worker = ChartWorker()
        self.worker.moveToThread(self.chart_thread)

        self.upload_file.connect(self.worker.load_file)
        self.worker.file_loaded.connect(self._show_filters)
        self.request_graph.connect(self.worker.generate_graph)
        self.worker.result_ready.connect(self._show_graph)

        self.chart_thread.start()

    def _add_labels(self):

        self.input_file_label = QLabel("Choose a file...", self)
        self.grid_layout.addWidget(self.input_file_label, 0, 4, Qt.AlignmentFlag.AlignTop)

    def _add_buttons(self):

        self.file_button = QPushButton("Select Excel File", self)
        self.file_button.clicked.connect(self._input_dialog)

        self.grid_layout.addWidget(
            self.file_button, 0, 4, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft
            )
    
    # Private Slots

    @Slot(list)
    def _show_filters(self, filter_data):

        cols = filter_data
        self.web.setHtml('<h1 style="text-align: left"> &#8593 Choose Your Data</h1>')

        self.x_label = QLabel("X Axis:", self)
        self.x_value = QComboBox(self)
        self.x_value.addItem("")
        self.x_value.addItems(cols)

        self.y_label = QLabel("Y Axis:", self)
        self.y_value = QComboBox(self)
        self.y_value.addItem("")
        self.y_value.addItems(cols)

        self.data_label = QLabel("Select Data Filter:", self)
        self.data_value = QComboBox(self)
        self.data_value.addItem("")
        self.data_value.addItems(cols)
        self.data_value.currentIndexChanged.connect(
            lambda: self.request_graph.emit(
                [
                    self.x_value.currentText(),
                    self.y_value.currentText(),
                    self.data_value.currentText()
                ]
            )
        )


        self.graph_button = QPushButton("Show Graph", self)
        self.graph_button.setMinimumHeight(50)
        self.graph_button.setMinimumWidth(100)
        self.graph_button.clicked.connect(
            lambda: self.request_graph.emit(
                [
                    self.x_value.currentText(), 
                    self.y_value.currentText(),
                    self.data_value.currentText()
                ]
            )
        )

        self.grid_layout.addWidget(
            self.x_label, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        ) 
        self.grid_layout.addWidget(
            self.x_value, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter
        )
        self.grid_layout.addWidget(
            self.y_label, 0, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft
        )
        self.grid_layout.addWidget(
            self.y_value, 0, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter
        )
        self.grid_layout.addWidget(
            self.data_label, 0, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter
        )
        self.grid_layout.addWidget(
            self.data_value, 0, 1, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter
        )
        self.grid_layout.addWidget(
            self.graph_button, 0, 2, Qt.AlignmentFlag.AlignCenter
            )

    @Slot(str)
    def _show_graph(self, temp_file):
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
            self.upload_file.emit(filename)
            self.input_file_label.setText(filename)
    
    @Slot()
    def _validate_and_request_graph(self, x_val, y_val, data_f):
        if not x_val and not y_val:
            self.web.setHtml("<h1 style='text-align: left'>Select your X and Y Data</h1>")

    # Public Functions

    def cleanup(self):
        if self.chart_thread.isRunning():
            self.chart_thread.quit()
            self.chart_thread.wait()
        if os.path.exists(os.path.abspath('temp_graph.html')):
            os.remove(os.path.abspath('temp_graph.html'))
        




        
