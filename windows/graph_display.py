import os

import pandas as pd
import plotly.express as px
import openpyxl as opx

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QPushButton,
    QWidget,
)


class ChartWorker(QObject):
    file_loaded = Signal(list)
    result_ready = Signal(str)

    def __init__(self):
        super().__init__()
        self.df: pd.DataFrame = None

    @Slot(str)
    def load_file(self, path):
        """Load Excel File (soon to update for CSV) into DataFrame

        Args:
            path (os.path): Path to file
        """

        # Read File into DataFrame
        filetype = path.split('.')[-1]
        match filetype:
            case "xlsx" | "xls":
                self.df = pd.read_excel(path, sheet_name=None)
            case "csv":
                self.df = pd.read_csv(path, sep=None, engine='python')

        # Get the data for the Window filters
        #! Update this to clean data and return better filtering data
        filter_data = self.df.columns

        # Send the filter data back to the Window
        self.file_loaded.emit(filter_data)

    @Slot(list)
    def generate_graph(self, filters):
        """Generate the html string to display the graph in the Window.

        Args:
            filters (list): Cleaned List containing x axis, y axis and data_filter
        """

        # Unpack the list
        x_data, y_data, data_filter = filters

        # Create the graph and layout
        fig = px.scatter(self.df, x=x_data, y=y_data, color=data_filter, title=y_data)
        fig.update_layout(title_x=0.5)
        if data_filter:
            fig.update_layout(showlegend=True)

        # Create the HTML string and output
        html_str = fig.to_html(include_plotlyjs="cdn")
        self.result_ready.emit(html_str)

        # USE BELOW IF USING OFFLINE. Comment above HTML based functions
        # temp_file = os.path.abspath("temp_graph.html")
        # fig.write_html(temp_file)


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
        """
        Start the Worker thread that will process the file and generate the graph html
        """

        # Initialize the thread and worker and push worker onto thread
        self.chart_thread = QThread()
        self.worker = ChartWorker()
        self.worker.moveToThread(self.chart_thread)

        # Connect the signals
        self.upload_file.connect(self.worker.load_file)
        self.worker.file_loaded.connect(self._show_filters)
        self.request_graph.connect(self.worker.generate_graph)
        self.worker.result_ready.connect(self._show_graph)

        # Start the thread
        self.chart_thread.start()

    def _add_labels(self):
        """Add the initial labels to the WIndow"""
        self.input_file_label = QLabel("Choose a file...", self)
        self.grid_layout.addWidget(
            self.input_file_label, 0, 4, Qt.AlignmentFlag.AlignTop
        )

    def _add_buttons(self):
        """Add the initial buttons the the Window"""
        self.file_button = QPushButton("Select Excel File", self)
        self.file_button.clicked.connect(self._input_dialog)

        self.grid_layout.addWidget(
            self.file_button,
            0,
            4,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
        )

    # Private Slots

    @Slot(list)
    def _show_filters(self, filter_data):
        """Show the filter data received from file_loaded thread signal

        Args:
            filter_data (list): List of data to be used as filters
        """

        # Currently only the columns come as filterable data
        cols = filter_data
        self.web.setHtml("<h1 style='text-indent: 10%''> &#8593 Choose Your Data</h1>")

        # Set up all of the filtering specific buttons and labels
        self.x_label = QLabel("X Axis:", self)
        self.x_value = QComboBox(self)
        self.x_value.addItem("")
        self.x_value.addItems(cols)
        self.x_value.currentIndexChanged.connect(
            lambda: self._validate_and_request_graph(
                self.x_value.currentText(),
                self.y_value.currentText(),
                self.data_value.currentText(),
            )
        )

        self.y_label = QLabel("Y Axis:", self)
        self.y_value = QComboBox(self)
        self.y_value.addItem("")
        self.y_value.addItems(cols)
        self.y_value.currentIndexChanged.connect(
            lambda: self._validate_and_request_graph(
                self.x_value.currentText(),
                self.y_value.currentText(),
                self.data_value.currentText(),
            )
        )

        self.data_label = QLabel("Select Data Filter:", self)
        self.data_value = QComboBox(self)
        self.data_value.addItem("")
        self.data_value.addItems(cols)
        self.data_value.currentIndexChanged.connect(
            lambda: self._validate_and_request_graph(
                self.x_value.currentText(),
                self.y_value.currentText(),
                self.data_value.currentText(),
            )
        )

        # Apply all filter Widgets to the grid
        self.grid_layout.addWidget(
            self.x_label, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight
        )
        self.grid_layout.addWidget(
            self.x_value, 0, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self.grid_layout.addWidget(
            self.y_label,
            0,
            0,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
        )
        self.grid_layout.addWidget(
            self.y_value,
            0,
            1,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
        )
        self.grid_layout.addWidget(
            self.data_label,
            0,
            2,
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        )
        self.grid_layout.addWidget(
            self.data_value,
            0,
            2,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
        )

    @Slot(str)
    def _show_graph(self, html_str):
        """Display the graph on the WebView

        Args:
            html_str (str): HTML String to be displayed
        """
        # file = QUrl.fromLocalFile(temp_file)
        # self.web.load(file)
        self.web.setHtml(html_str)

    @Slot()
    def _input_dialog(self):
        """Opens the input dialog for the data file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Choose File...",
            "",
            "Excel (*.xlsx *.xls);;CSV (*.csv);;All Files (*)",
        )
        if filename:
            self.upload_file.emit(filename)
            self.input_file_label.setText(filename.split('/')[-1])

    @Slot()
    def _validate_and_request_graph(self, x_val, y_val, data_f):
        """Check the inputs of the filter data and requests graph if valid

        Args:
            x_val (str): X Axis value
            y_val (str): Y Axis value
            data_f (str): Data to color the points by
        """
        if x_val and y_val:
            if not data_f:
                data_f = None
            self.request_graph.emit([x_val, y_val, data_f])
            self.web.setHtml("<h4 style='text-align: center'>Loading Graph...</h4>")
        elif x_val or y_val:
            if data_f:
                self.web.setHtml(
                    "<h1 style='text-indent: 10%'>&#8593 Choose X and Y</h1>"
                )
        else:
            self.web.setHtml("<h1 style='text-indent: 10%'>&#8593 Choose X and Y</h1>")

    # Public Functions

    def cleanup(self):
        """Terminates the thread and deletes the temporary html file if used."""
        if self.chart_thread.isRunning():
            self.chart_thread.quit()
            self.chart_thread.wait()
        if os.path.exists(os.path.abspath("temp_graph.html")):
            os.remove(os.path.abspath("temp_graph.html"))
