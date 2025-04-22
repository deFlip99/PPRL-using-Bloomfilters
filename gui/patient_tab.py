import os
from functools import partial

from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QTableWidget, QTableWidgetItem, QComboBox, QFileDialog,
    QHeaderView, QCheckBox, QPlainTextEdit, QSizePolicy, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics

from config import PATHS
from gui.gui_utils import (
    fetch_all_patients,
    load_stylesheet,
    create_button,
    format_date,
    fetch_pid_table_names
)
from gui.AddPatientDialog import AddPatientDialog
from backend.database import (
    db_insert_patient,
    db_export_patient_to_file,
    db_export_patient_into_pid,
    db_delete_patient,
    db_lookup_name,
    db_insert_patient_from_file
)


class PatientenTab(QWidget):
    def __init__(self, pid_tab):
        super().__init__()
        self.pid_tab = pid_tab
        self.header_all_checked = False

        self.setupUI()
        self.setStyleSheet(load_stylesheet("patient_tab.qss"))

        # Signal PIDTab
        self.pid_tab.pid_tables_updated.connect(self.load_pid_table_names)

    def setupUI(self):
        main_layout = QGridLayout(self)


        # Button: add patient
        self.add_patient_button = create_button(
            "Patient hinzufügen",
            "Neuen Patienten hinzufügen",
            self.open_add_patient_dialog
        )
        main_layout.addWidget(self.add_patient_button, 0, 0, 1, 2)

        # Button: patients from file
        self.import_patient_file_button = create_button(
            "Patienten Datei einlesen",
            "Ließt Patientendaten aus einer CSV oder JSON Datei ",
            self.import_patient_from_file
        )
        self.import_patient_file_button.setObjectName("importFileButton")
        
        main_layout.addWidget(self.import_patient_file_button, 0, 2, 1, 2)


        # Button: delete patients
        self.delete_patients_button = create_button(
            "Patienten entfernen",
            "Entfernt alle ausgewählten Patienten aus der Datenbank",
            self.remove_selected_patients
        )
        self.delete_patients_button.setObjectName("removeButton")

        main_layout.addWidget(self.delete_patients_button, 0, 4, 1, 2)


        # Button: export to pidDB
        self.pid_export_button = create_button(
            "Patienten in pidDB übertragen",
            "Ausgewählte Patienten in die PID-Datenbank exportieren",
            self.export_to_pid
        )
        main_layout.addWidget(self.pid_export_button, 1, 0, 1, 3)

        # Dropdown: Pid-Tables
        self.pid_table_dropdown = QComboBox()
        self.pid_table_dropdown.setEditable(False)
        self.pid_table_dropdown.setToolTip("Vorhandene PID-Tabellen auswählen")
        main_layout.addWidget(self.pid_table_dropdown, 1, 3, 1, 3)

        # Button: export Bloomfilter
        self.export_checked_bf_button = create_button(
            "Bloomfilter exportieren",
            "Exportiert die Bloomfilter aller ausgewählten Patienten in eine Datei",
            self.export_checked_bloomfilters
        )
        main_layout.addWidget(self.export_checked_bf_button, 2, 0, 1, 3)

        # Dropdown: file format
        self.export_format_dropdown = QComboBox()
        self.export_format_dropdown.addItems(["CSV", "JSON"])
        self.export_format_dropdown.setToolTip("Dateiformat für den Export auswählen")
        self.export_format_dropdown.setCurrentIndex(0)
        main_layout.addWidget(self.export_format_dropdown, 2, 3, 1, 3)


        # Tabelle
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "☑",
            "Vorname", "Nachname", "Geburtsdatum", "Geschlecht", "MDAT", "Bloomfilter"
        ])
        self.table.setSortingEnabled(True)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # select all
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_section_clicked)

        # resize verticalHeader
        header = self.table.verticalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        # widget height
        example_widget = QPlainTextEdit()
        fm_widget = QFontMetrics(example_widget.font())
        fixed_height = int(fm_widget.lineSpacing() * 3 + 5)
        header.setDefaultSectionSize(fixed_height)

        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        main_layout.addWidget(self.table, 3, 0, 1, 5)
        self.setLayout(main_layout)

        # Data: initialize
        self.load_pid_table_names()
        self.load_data()

    def on_header_section_clicked(self, logical_index):
        if logical_index == 0:
            self.header_all_checked = not self.header_all_checked
            row_count = self.table.rowCount()
            for row in range(row_count):
                cell_widget_cb = self.table.cellWidget(row, 0)
                if cell_widget_cb:
                    checkbox = cell_widget_cb.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(self.header_all_checked)

    def adjust_column_widths(self):
        header = self.table.horizontalHeader()
        total_width = self.table.viewport().width()

        COLUMN_WIDTH_RATIOS = [0.04, 0.1, 0.1, 0.1, 0.1, 0.4, 0.16]
        for i, ratio in enumerate(COLUMN_WIDTH_RATIOS):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(i, int(total_width * ratio))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_column_widths()

    def load_data(self):
        patients = fetch_all_patients(PATHS.DATABASE_PATH_PATIENT)
        self.table.setRowCount(len(patients))

        example_widget = QPlainTextEdit()
        fm_widget = QFontMetrics(example_widget.font())
        fixed_height = int(fm_widget.lineSpacing() * 3 + 5)

        for row_idx, row_data in enumerate(patients):
            checkbox = QCheckBox()
            cell_widget_cb = QWidget()
            layout_cb = QGridLayout(cell_widget_cb)
            layout_cb.addWidget(checkbox, 0, 0, 1, 1)
            layout_cb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_cb.setContentsMargins(0, 0, 0, 0)
            cell_widget_cb.setLayout(layout_cb)
            self.table.setCellWidget(row_idx, 0, cell_widget_cb)

            # Spalten: 1 (Vorname), 2 (Nachname), 3 (Geburtsdatum), 4 (Geschlecht)
            for col_offset in range(4):
                if col_offset == 2:  # Geburtsdatum formatieren (Index 2 in row_data)
                    raw_date = row_data[col_offset]
                    formatted_date = format_date(raw_date)
                    item = QTableWidgetItem(formatted_date)
                    item.setData(Qt.ItemDataRole.UserRole, int(raw_date))
                else:
                    item = QTableWidgetItem(str(row_data[col_offset]))

                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                item.setToolTip(str(row_data[col_offset]))
                self.table.setItem(row_idx, col_offset + 1, item)

            # MDAT
            mdat_text = str(row_data[4])
            mdat_widget = QPlainTextEdit()
            mdat_widget.setReadOnly(True)
            mdat_widget.setPlainText(mdat_text)
            mdat_widget.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            mdat_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            mdat_widget.setToolTip(mdat_text)
            mdat_widget.setFixedHeight(fixed_height)
            self.table.setCellWidget(row_idx, 5, mdat_widget)

            # Bloomfilter-Download-Button
            button = create_button(
                "Download",
                "Bloomfilter für diesen Patienten herunterladen",
                partial(self.export_bf, row_data[0], row_data[1])
            )
            cell_widget_btn = QWidget()
            layout_btn = QGridLayout(cell_widget_btn)
            layout_btn.addWidget(button, 0, 0, 1, 1)
            layout_btn.setContentsMargins(0, 0, 0, 0)
            layout_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell_widget_btn.setLayout(layout_btn)
            self.table.setCellWidget(row_idx, 6, cell_widget_btn)

            # Row height
            self.table.setRowHeight(row_idx, fixed_height)

    def load_pid_table_names(self):
        tables = fetch_pid_table_names(PATHS.DATABASE_PATH_PID)
        self.pid_table_dropdown.clear()
        self.pid_table_dropdown.addItems(tables)

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
        self.load_data()

    def remove_selected_patients(self):
        row_count = self.table.rowCount()
        patient_ids_to_delete = []

        for row_idx in range(row_count):
            cell_widget_cb = self.table.cellWidget(row_idx, 0)
            if not cell_widget_cb:
                continue
            checkbox = cell_widget_cb.findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                first_name_item = self.table.item(row_idx, 1)
                last_name_item = self.table.item(row_idx, 2)
                if first_name_item and last_name_item:
                    fname = first_name_item.text()
                    lname = last_name_item.text()
                    results = db_lookup_name((fname, lname), ["patienten_id"])
                    for row_tuple in results:
                        pid = row_tuple[0]
                        patient_ids_to_delete.append(pid)

        if not patient_ids_to_delete:
            print("Keine Patienten ausgewählt oder keine passenden Einträge gefunden.")
            return

        try:
            db_delete_patient(patient_ids_to_delete)
            self.load_data()
        except Exception as e:
            print(f"Fehler beim Löschen von Patienten: {e}")

    def export_to_pid(self):
        pid_table_name = self.pid_table_dropdown.currentText()
        if not pid_table_name:
            return

        selected_patients = []
        row_count = self.table.rowCount()
        for row_idx in range(row_count):
            cell_widget_cb = self.table.cellWidget(row_idx, 0)
            if not cell_widget_cb:
                continue
            checkbox = cell_widget_cb.findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                first_name_item = self.table.item(row_idx, 1)
                last_name_item = self.table.item(row_idx, 2)
                if first_name_item and last_name_item:
                    selected_patients.append(
                        (first_name_item.text(), last_name_item.text())
                    )

        if not selected_patients:
            return

        try:
            db_export_patient_into_pid(selected_patients, pid_table_name)
        except Exception as e:
            print(f"Fehler beim Export in die PID-Tabelle '{pid_table_name}': {e}")


    def export_checked_bloomfilters(self):

        export_format = self.export_format_dropdown.currentText().lower()

        selected_patients = []
        row_count = self.table.rowCount()
        for row_idx in range(row_count):
            cell_widget_cb = self.table.cellWidget(row_idx, 0)
            if not cell_widget_cb:
                continue
            checkbox = cell_widget_cb.findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                first_name_item = self.table.item(row_idx, 1)
                last_name_item = self.table.item(row_idx, 2)
                if first_name_item and last_name_item:
                    selected_patients.append(
                        (first_name_item.text(), last_name_item.text())
                    )

        if not selected_patients:
            return

        try:
            if len(selected_patients) == 1:
                fn, ln = selected_patients[0]
                db_export_patient_to_file(fn, ln, export_format)
            else:
                first_names = [p[0] for p in selected_patients]
                last_names = [p[1] for p in selected_patients]
                db_export_patient_to_file(first_names, last_names, export_format)
        except Exception as e:
            print(f"Fehler beim Exportieren der Bloomfilter: {e}")


    def export_bf(self, first_name: str, last_name: str):
        try:
            export_format = self.export_format_dropdown.currentText().lower()
            db_export_patient_to_file(first_name, last_name, export_format)
            print(f"Bloomfilter für {first_name} {last_name} exportiert.")
        except Exception as e:
            print(f"Fehler beim Exportieren des Bloomfilters für {first_name} {last_name}: {e}")


    def import_patient_from_file(self):

        file_filter = "CSV or JSON Files (*.csv *.json)"
        initial_dir = PATHS.IMPORT_DIR

        # data dialog
        file_path, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Patientendatei auswählen",
            directory=initial_dir,
            filter=file_filter
        )

        if not file_path:
            print("Abgebrochen oder keine Datei gewählt.")
            return

        # check file extension
        _, extension = os.path.splitext(file_path)
        extension = extension.lower()

        if extension == ".csv":
            file_format = "csv"
        elif extension == ".json":
            file_format = "json"
        else:
            print(f"Dateiformat {extension} wird nicht unterstützt. Bitte CSV oder JSON wählen.")
            return

        try:
            db_insert_patient_from_file(
                filename="",
                file_path=file_path,
                file_format=file_format
            )
            print(f"Datei '{file_path}' erfolgreich eingelesen.")
        except Exception as e:
            print(f"Fehler beim Einlesen der Datei '{file_path}': {e}")

        self.load_data()