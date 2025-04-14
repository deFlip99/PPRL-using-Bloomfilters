import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QTableWidget, QTableWidgetItem, QComboBox, QPushButton,
    QHeaderView, QCheckBox, QPlainTextEdit, QSizePolicy, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics
from config import PATHS
from gui.gui_utils import fetch_all_patients, load_stylesheet, create_button, format_date, fetch_pid_table_names
from gui.AddPatientDialog import AddPatientDialog
from backend.database import db_insert_patient, db_export_patient_to_file, db_export_patient_into_pid
from functools import partial

class PatientenTab(QWidget):
    def __init__(self, pid_tab):
        super().__init__()
        self.pid_tab = pid_tab  # Referenz zu PIDTab
        self.setupUI()
        self.setStyleSheet(load_stylesheet("patient_tab.qss"))

        # Signal von PIDTab mit PatientenTab verbinden
        self.pid_tab.pid_tables_updated.connect(self.load_pid_table_names)


    def setupUI(self):
        # Hauptlayout mit QGridLayout
        main_layout = QGridLayout(self)

        # Button zum Hinzufügen eines Patienten
        self.add_patient_button = create_button(
            "Patient hinzufügen",
            "Neuen Patienten hinzufügen",
            self.open_add_patient_dialog
        )
        main_layout.addWidget(self.add_patient_button, 0, 0)

        # Dropdown-Menü für Export-Format
        self.export_format_dropdown = QComboBox()
        self.export_format_dropdown.addItems(["CSV", "JSON"])
        self.export_format_dropdown.setToolTip("Dateiformat für den Export auswählen")
        self.export_format_dropdown.setCurrentIndex(0)
        main_layout.addWidget(self.export_format_dropdown, 0, 1)

        # Button und Dropdown-Menü für PID-Export
        self.pid_export_button = create_button(
            "Zu Pid Exportieren",
            "Exportieren der Patientendaten in die PID-Datenbank",
            self.export_to_pid
        )
        main_layout.addWidget(self.pid_export_button, 1, 0)

        self.pid_table_dropdown = QComboBox()
        self.pid_table_dropdown.setEditable(False)  # Nur Auswahl aus vorhandenen Einträgen erlauben
        self.pid_table_dropdown.setToolTip("Vorhandene PID-Tabellen auswählen")
        self.load_pid_table_names()  # Lade PID-Tabellen
        main_layout.addWidget(self.pid_table_dropdown, 1, 1)

        # Tabelle für Patientendaten
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "", "Vorname", "Nachname", "Geburtsdatum", "Geschlecht", "MDAT", "Bloomfilter"
        ])
        self.table.setSortingEnabled(True)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header = self.table.verticalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        # Feste Höhe für Zeilen
        example_widget = QPlainTextEdit()
        fm_widget = QFontMetrics(example_widget.font())
        fixed_height = int(fm_widget.lineSpacing() * 3 + 5)
        header.setDefaultSectionSize(fixed_height)

        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        main_layout.addWidget(self.table, 2, 0, 1, 2)
        self.load_data()



    def adjust_column_widths(self):
        header = self.table.horizontalHeader()
        total_width = self.table.viewport().width()

        COLUMN_WIDTH_RATIOS = [0.02, 0.1, 0.1, 0.1, 0.1, 0.4, 0.18]

        for i, ratio in enumerate(COLUMN_WIDTH_RATIOS):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(i, int(total_width * ratio))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_column_widths()

    def load_data(self):
        # Die Patientendaten laden und in die Tabelle einfügen
        patients = fetch_all_patients(PATHS.DATABASE_PATH_PATIENT)
        self.table.setRowCount(len(patients))

        # Festlegen einer einheitlichen Zeilenhöhe (basiert auf MDAT-Höhe)
        example_widget = QPlainTextEdit()
        fm_widget = QFontMetrics(example_widget.font())
        fixed_height = int(fm_widget.lineSpacing() * 3 + 5)

        for row_idx, row_data in enumerate(patients):
            # Checkbox erstellen
            checkbox = QCheckBox()
            cell_widget_cb = QWidget()
            layout_cb = QGridLayout(cell_widget_cb)
            layout_cb.addWidget(checkbox, 0, 0, 1, 1)
            layout_cb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_cb.setContentsMargins(0, 0, 0, 0)
            cell_widget_cb.setLayout(layout_cb)
            self.table.setCellWidget(row_idx, 0, cell_widget_cb)

            # Daten in die Tabelle einfügen
            for col_offset in range(4):  # Bearbeitung der ersten 4 Spalten
                if col_offset == 2:  # Geburtsdatum formatieren
                    raw_date = row_data[col_offset]
                    formatted_date = format_date(raw_date)
                    item = QTableWidgetItem(formatted_date)
                    item.setData(Qt.ItemDataRole.UserRole, int(raw_date))  # Für Sortierung YYYYMMDD
                else:
                    item = QTableWidgetItem(str(row_data[col_offset]))

                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                item.setToolTip(str(row_data[col_offset]))
                self.table.setItem(row_idx, col_offset + 1, item)

            # MDAT erstellen und hinzufügen
            mdat_text = str(row_data[4])
            mdat_widget = QPlainTextEdit()
            mdat_widget.setReadOnly(True)
            mdat_widget.setPlainText(mdat_text)
            mdat_widget.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            mdat_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            mdat_widget.setToolTip(mdat_text)
            mdat_widget.setFixedHeight(fixed_height)  # Feste Höhe setzen
            self.table.setCellWidget(row_idx, 5, mdat_widget)

            # Bloomfilter-Download-Button erstellen und hinzufügen
            button = create_button(
                "Download",
                "Bloomfilter für diesen Patienten herunterladen",
                partial(self.export_bf, row_data[0], row_data[1])
            )
            cell_widget_btn = QWidget()
            layout_btn = QGridLayout(cell_widget_btn)
            layout_btn.addWidget(button, 0, 0, 1, 1)  # Button zentriert
            cell_widget_btn.setLayout(layout_btn)
            self.table.setCellWidget(row_idx, 6, cell_widget_btn)

            # Höhe der Zeile festlegen
            self.table.setRowHeight(row_idx, fixed_height)

    def load_pid_table_names(self):
        tables = fetch_pid_table_names(PATHS.DATABASE_PATH_PID)
        self.pid_table_dropdown.clear()
        self.pid_table_dropdown.addItems(tables)




    def export_to_pid(self):
        """Exportiere Patienten in die ausgewählte PID-Tabelle."""
        pid_table_name = self.pid_table_dropdown.currentText()  # Ausgewählte Tabelle
        all_patients = fetch_all_patients(PATHS.DATABASE_PATH_PATIENT)  # Alle Patientendaten abrufen


        selected_patients = [(row[0], row[1]) for row in all_patients if len(row) >= 2]

        if not selected_patients:
            print("Fehler: in export_pid")
            return

        # Export in die PID-Datenbank
        try:
            db_export_patient_into_pid(selected_patients, pid_table_name)
        except Exception as e:
            print(f"Fehler beim Exportieren in die PID-Tabelle '{pid_table_name}': {e}")

    def open_add_patient_dialog(self):
        dialog = AddPatientDialog()
        if dialog.exec():
            data = dialog.get_patient_data()
            self.add_patient_to_database(data)

    def add_patient_to_database(self, data):
        db_insert_patient(
            first_name=data["first_name"],
            last_name=data["last_name"],
            date_of_birth=data["date_of_birth"],
            gender=data["gender"],
            mdat=data["mdat"]
        )
        self.load_data()  # Tabelle aktualisieren

    def export_bf(self, first_name, last_name):
        try:
            export_format = self.export_format_dropdown.currentText().lower()  # "csv" oder "json"
            db_export_patient_to_file(first_name, last_name, export_format)
        except Exception as e:
            print(f"Fehler beim Exportieren des Bloomfilters für {first_name} {last_name}: {e}")