import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QTableWidget, QCheckBox,
    QPlainTextEdit, QPushButton, QComboBox, QSizePolicy, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFontMetrics
from config import PATHS, GLOBAL_VAL
from backend.database import db_add_pid_table, db_delete_pid_table
from gui.AddTableDialog import AddTableDialog
from gui.DeleteTableDialog import DeleteTableDialog
from gui.gui_utils import fetch_pid_table_names, load_stylesheet

class PIDTab(QWidget):
    pid_tables_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.resize_timer = QTimer()
        self.resize_timer.setInterval(80)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.adjust_column_widths)
        self.setStyleSheet(load_stylesheet("pid_tab.qss"))
        self.conn = sqlite3.connect(PATHS.DATABASE_PATH_PID)
        self.cursor = self.conn.cursor()

        self.setupUI()
        self.load_table_names()


    def setupUI(self):
        # Hauptlayout mit QGridLayout
        main_layout = QGridLayout(self)

        # Dropdown-Menü oben
        self.dropdown = QComboBox()
        self.dropdown.currentTextChanged.connect(self.load_data)
        main_layout.addWidget(self.dropdown, 0, 0)  # Position links im Layout

        # Knopf für das Erstellen eines neuen Tables
        self.add_table_button = QPushButton("Neues Table erstellen")
        self.add_table_button.setToolTip("Ein neues PID-Table in der Datenbank erstellen")
        self.add_table_button.clicked.connect(self.create_new_pid_table)
        main_layout.addWidget(self.add_table_button, 0, 1)  # Position rechts neben dem Dropdown

        # Knopf für das Löschen einer Tabelle
        self.delete_table_button = QPushButton("Tabelle löschen")
        self.delete_table_button.setToolTip("Die aktuell ausgewählte Tabelle löschen")
        self.delete_table_button.clicked.connect(self.delete_selected_table)
        main_layout.addWidget(self.delete_table_button, 1, 0, 1, 2)  # Unterhalb des Hinzufügen-Knopfes

        # Tabelle für PID-Daten
        self.table = QTableWidget()
        self.table.setColumnCount(4)  # Spalte für Relink hinzugefügt
        self.table.setHorizontalHeaderLabels(["", "MDAT", "Bloomfilter", "Relink"])

        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Tabelle ins Layout einfügen
        main_layout.addWidget(self.table, 2, 0, 1, 2)

        self.setLayout(main_layout)


    def load_table_names(self):
        tables = fetch_pid_table_names(PATHS.DATABASE_PATH_PID)
        self.dropdown.clear()
        self.dropdown.addItems(tables)

        if tables:
            self.load_data(tables[0])
        else:
            self.table.setRowCount(0)


    def load_data(self, table_name):
        if not table_name:
            return

        table_name = GLOBAL_VAL.PID_TABLE_PREFIX + table_name

        # Lese nur mdat und BFS
        query = f"SELECT mdat, BFS FROM {table_name}"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        self.table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            # Checkbox
            checkbox = QCheckBox()
            cell_widget_cb = QWidget()
            layout_cb = QGridLayout(cell_widget_cb)
            layout_cb.addWidget(checkbox, 0, 0)
            layout_cb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_cb.setContentsMargins(0, 0, 0, 0)
            cell_widget_cb.setLayout(layout_cb)
            self.table.setCellWidget(row_idx, 0, cell_widget_cb)

            # MDAT
            mdat_text = str(row_data[0])
            mdat_widget = QPlainTextEdit()
            mdat_widget.setReadOnly(True)
            mdat_widget.setPlainText(mdat_text)
            mdat_widget.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            mdat_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            fm = QFontMetrics(mdat_widget.font())
            height = fm.lineSpacing() * 3 + 8
            mdat_widget.setFixedHeight(height)
            self.table.setCellWidget(row_idx, 1, mdat_widget)
            self.table.setRowHeight(row_idx, height)

            # Bloomfilter-Download-Button
            download_button = QPushButton("Download")
            download_button.setToolTip("Bloomfilter herunterladen")
            download_button.setFixedWidth(150)

            download_cell_widget = QWidget()
            download_layout = QGridLayout(download_cell_widget)
            download_layout.addWidget(download_button)
            download_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            download_layout.setContentsMargins(5, 2, 5, 2)
            self.table.setCellWidget(row_idx, 2, download_cell_widget)

            # Relink-Button
            relink_button = QPushButton("Relink")
            relink_button.setToolTip("Relink-Funktion ausführen")
            relink_button.setFixedWidth(150)

            relink_cell_widget = QWidget()
            relink_layout = QGridLayout(relink_cell_widget)
            relink_layout.addWidget(relink_button)
            relink_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            relink_layout.setContentsMargins(5, 2, 5, 2)
            self.table.setCellWidget(row_idx, 3, relink_cell_widget)

        # Nach dem Befüllen, die Spaltenbreiten dynamisch setzen
        self.adjust_column_widths()
    
    
    def delete_selected_table(self):
        # Name aus DropDown Menü
        selected_table = self.dropdown.currentText()

        if not selected_table:
            print("Keine Tabelle ausgewählt.")
            return

        # Bestätigungsdialog
        dialog = DeleteTableDialog(selected_table, self)
        while True:
            if dialog.exec():
                result = db_delete_pid_table(selected_table)
                if result == 0:
                    dialog.show_error_message("Die Tabelle 'main' kann nicht gelöscht werden.")
                    continue  # Dialog offen lassen
                else:
                    self.load_table_names()
                    break
            else:
                break


    def create_new_pid_table(self):
        dialog = AddTableDialog(self)
        while dialog.exec():  # Schleife für erneute Eingabe
            table_name = dialog.get_table_name()  # Eingabe abrufen

            if table_name:
                result = db_add_pid_table(table_name)
                if result == 0:
                    dialog.show_error_message("Ungültiger Tabellenname")
                else:
                    self.load_table_names()
                    self.pid_tables_updated.emit()  # Signal auslösen
                    break
            else:
                dialog.show_error_message("Bitte geben Sie einen Namen ein.")



    def adjust_column_widths(self):
        header = self.table.horizontalHeader()
        total_width = self.table.viewport().width()


        COLUMN_WIDTH_RATIOS = [0.02, 0.48, 0.25 , 0.25]

        for i, ratio in enumerate(COLUMN_WIDTH_RATIOS):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(i, int(total_width * ratio))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_timer.start()

    def __del__(self):
        if self.conn:
            self.conn.close()