from PySide6.QtWidgets import (QWidget,
                               QPushButton,
                               QLabel,
                               QGridLayout,
                               QFileDialog,
                               QComboBox)
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
        filter_data = [self.df.columns, self.df.Room.unique()]
        self.file_loaded.emit(filter_data)

    @Slot(list)
    def generate_graph(self, filters):

        temp_file = os.path.abspath("temp_chart.html")
        x_data, y_data, room = filters
        graph_df = self.df[self.df.Room == room]
        fig = px.scatter(graph_df, x=x_data, y=y_data)
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

        cols, rooms = filter_data
        self.web.setHtml('<h1 style="text-align: left">Choose Your Data &#8593</h1>')

        self.x_label = QLabel("X Axis: ", self)
        self.x_value = QComboBox(self)
        self.x_value.addItem("Select X-Axis")
        self.x_value.addItems(cols)

        self.y_label = QLabel("Y Axis: ", self)
        self.y_value = QComboBox(self)
        self.y_value.addItem("Select Y-Axis")
        self.y_value.addItems(cols)

        self.room_value = QComboBox(self)
        self.room_value.addItems(rooms)

        self.graph_button = QPushButton("Show Graph", self)
        self.graph_button.clicked.connect(
            lambda: self.request_graph.emit(
                [
                    self.x_value.currentText(), 
                    self.y_value.currentText(),
                    self.room_value.currentText()
                ]
            )
        )

        self.grid_layout.addWidget(
            self.graph_button, 0, 2, Qt.AlignmentFlag.AlignCenter
            )
        self.grid_layout.addWidget(
            self.x_label, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.grid_layout.addWidget(
            self.x_value, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )
        self.grid_layout.addWidget(
            self.y_label, 0, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft
        )
        self.grid_layout.addWidget(
            self.y_value, 0, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight
        )
        self.grid_layout.addWidget(
            self.room_value, 0, 1, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter
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

    # Public Functions

    def cleanup(self):
        if self.chart_thread.isRunning():
            self.chart_thread.quit()
            self.chart_thread.wait()
        if os.path.exists(os.path.abspath('temp_chart.html')):
            os.remove(os.path.abspath('temp_chart.html'))
        




        
