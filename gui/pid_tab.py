import sqlite3
from functools import partial

from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QTableWidget, QCheckBox, QPlainTextEdit,
    QPushButton, QComboBox, QSizePolicy, QHeaderView, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFontMetrics

from config import PATHS, GLOBAL_VAL
from backend.database import (
    db_add_pid_table,
    db_delete_pid_table,
    db_clear_pid_table
)
from gui.AddTableDialog import AddTableDialog
from gui.DeleteTableDialog import DeleteTableDialog
from gui.RelinkDialog import RelinkDialog
from gui.gui_utils import (
    fetch_pid_table_names,
    load_stylesheet,
    create_button
)


class PIDTab(QWidget):

    pid_tables_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.resize_timer = QTimer()
        self.resize_timer.setInterval(80)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.adjust_column_widths)
        self.setStyleSheet(load_stylesheet("pid_tab.qss"))

        # Datenbank-Verbindung öffnen
        self.conn = sqlite3.connect(PATHS.DATABASE_PATH_PID)
        self.cursor = self.conn.cursor()

        self.setupUI()
        self.load_pid_table_names()


    def setup_pat_signal(self, pat_tab):
        # Signal PIDTab
        self.pat_tab = pat_tab
        self.pat_tab.pat_tables_updated.connect(self.load_data)


    def setupUI(self):

        main_layout = QGridLayout(self)

        # Dropdown: pid-table selection
        self.dropdown = QComboBox()
        self.dropdown.currentTextChanged.connect(self.load_data)
        main_layout.addWidget(self.dropdown, 0, 0)

        # Button: add new table
        self.add_table_button = create_button(
            "Neue Tabelle erstellen",
            "Ein neues PID-Table in der Datenbank erstellen",
            self.create_new_pid_table
        )
        self.add_table_button.setObjectName("addTableButton")
        main_layout.addWidget(self.add_table_button, 0, 1)

        # Button: delete table
        self.delete_table_button = create_button(
            "Tabelle löschen",
            "Die aktuell ausgewählte Tabelle löschen",
            self.delete_selected_table
        )
        self.delete_table_button.setObjectName("deleteTableButton")
        main_layout.addWidget(self.delete_table_button, 1, 0)

        # Button: clear table
        self.clear_table_button = create_button(
            "Tabelle leeren",
            "Alle Einträge der aktuell ausgewählten Tabelle löschen",
            self.clear_selected_table
        )
        self.clear_table_button.setObjectName("clearTableButton")
        main_layout.addWidget(self.clear_table_button, 1, 1)

        #PID-Daten
        self.table = QTableWidget()
        #0 = Checkbox, 1 = MDAT, 2 = Bloomfilter-Button, 3 = Relink-Button
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["☑", "MDAT", "Bloomfilter", "Relink"])
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        main_layout.addWidget(self.table, 2, 0, 1, 2)
        self.setLayout(main_layout)

    def load_pid_table_names(self):
        tables = fetch_pid_table_names(PATHS.DATABASE_PATH_PID)
        self.dropdown.clear()
        self.dropdown.addItems(tables)
        if tables:
            # Standardmäßig erste Tabelle laden
            self.load_data(tables[0])
        else:
            self.table.setRowCount(0)

    def load_data(self, table_name = None):
        if not table_name:
            table_name = self.dropdown.currentText()

        full_table_name = GLOBAL_VAL.PID_TABLE_PREFIX + table_name
        query = f"SELECT mdat, BFS FROM {full_table_name}"
        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
        except Exception as e:
            print(f"Fehler beim Laden der Tabelle {full_table_name}: {e}")
            return

        self.table.setRowCount(len(rows))

        # Beispiel-Widget, um die Zeilenhöhe zu bestimmen
        example_widget = QPlainTextEdit()
        fm_widget = QFontMetrics(example_widget.font())
        fixed_height = int(fm_widget.lineSpacing() * 3 + 8)

        for row_idx, (mdat, bfs) in enumerate(rows):
            #Checkbox
            checkbox = QCheckBox()
            checkbox_widget = QWidget()
            checkbox_layout = QGridLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_widget.setLayout(checkbox_layout)
            self.table.setCellWidget(row_idx, 0, checkbox_widget)

            #MDAT 
            mdat_widget = QPlainTextEdit()
            mdat_widget.setReadOnly(True)
            mdat_widget.setPlainText(str(mdat))
            mdat_widget.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            mdat_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            mdat_widget.setFixedHeight(fixed_height)
            self.table.setCellWidget(row_idx, 1, mdat_widget)

            #Download-Button (für BFS)
            download_bf_button = create_button(
                "Download",
                "Bloomfilter herunterladen",
                partial(self.export_bf, bfs)
            )
            download_bf_button.setFixedWidth(100)
            download_bf_widget = QWidget()
            download_bf_layout = QGridLayout(download_bf_widget)
            download_bf_layout.addWidget(download_bf_button)
            download_bf_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            download_bf_layout.setContentsMargins(5, 2, 5, 2)
            download_bf_widget.setLayout(download_bf_layout)
            self.table.setCellWidget(row_idx, 2, download_bf_widget)

            # Relink-Button
            relink_button = create_button(
                "Relink",
                "Relinks the Bloomfilter back to the original patient",
                partial(self.relink_event, bfs)
            )
            relink_button.setObjectName("relinkButton")
            relink_button.setFixedWidth(100)

            relink_cell_widget = QWidget()
            relink_layout = QGridLayout(relink_cell_widget)
            relink_layout.addWidget(relink_button)
            relink_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            relink_layout.setContentsMargins(5, 2, 5, 2)
            relink_cell_widget.setLayout(relink_layout)
            self.table.setCellWidget(row_idx, 3, relink_cell_widget)

            self.table.setRowHeight(row_idx, fixed_height)

    def export_bf(self, bfs: bytes):
        print("Noch keine Funktionalität")

    def relink_event(self, bfs: bytes):
        dialog = RelinkDialog(bfs)
        dialog.exec()

    def delete_selected_table(self):
        selected_table = self.dropdown.currentText()
        if not selected_table:
            print("Keine Tabelle ausgewählt.")
            return

        dialog = DeleteTableDialog(selected_table, self)
        while True:
            if dialog.exec():
                result = db_delete_pid_table(selected_table)
                if result == 0:
                    dialog.show_error_message("Diese Tabelle kann nicht gelöscht werden oder existiert nicht.")
                    continue
                else:
                    self.load_pid_table_names()
                    break
            else:
                break

    def clear_selected_table(self):
        selected_table = self.dropdown.currentText()
        if not selected_table:
            print("Keine Tabelle ausgewählt.")
            return

        try:
            db_clear_pid_table(selected_table)
            self.load_data(selected_table)
            print(f"Tabelle '{selected_table}' erfolgreich geleert.")
        except Exception as e:
            print(f"Fehler beim Leeren der Tabelle '{selected_table}': {e}")

    def create_new_pid_table(self):
        dialog = AddTableDialog(self)
        while dialog.exec():
            table_name = dialog.get_table_name()
            if table_name:
                result = db_add_pid_table(table_name)
                if result == 0:
                    dialog.show_error_message("Ungültiger Tabellenname oder Tabelle existiert bereits.")
                else:
                    self.load_pid_table_names()
                    self.pid_tables_updated.emit()
                    break
            else:
                dialog.show_error_message("Bitte einen gültigen Namen eingeben.")

    def adjust_column_widths(self):
        header = self.table.horizontalHeader()
        total_width = self.table.viewport().width()
        #Checkbox, MDAT, Bloomfilter-Button, Relink-Button
        COLUMN_WIDTH_RATIOS = [0.05, 0.45, 0.25, 0.25]
        for i, ratio in enumerate(COLUMN_WIDTH_RATIOS):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(i, int(total_width * ratio))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_timer.start()

    def __del__(self):
        if self.conn:
            self.conn.close()
