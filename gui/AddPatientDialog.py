from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QPushButton, QDateEdit
from PyQt6.QtCore import QDate

class AddPatientDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Patient hinzufügen")
        self.setMinimumSize(400, 300)
        self.setupUI()

    def setupUI(self):
        layout = QFormLayout(self)

        self.first_name_input = QLineEdit()
        layout.addRow("Vorname:", self.first_name_input)

        self.last_name_input = QLineEdit()
        layout.addRow("Nachname:", self.last_name_input)

        self.date_of_birth_input = QDateEdit()
        self.date_of_birth_input.setCalendarPopup(True)
        self.date_of_birth_input.setDate(QDate.currentDate())
        layout.addRow("Geburtsdatum:", self.date_of_birth_input)

        self.gender_input = QComboBox()
        self.gender_input.addItems(["männlich", "weiblich", "divers"])
        layout.addRow("Geschlecht:", self.gender_input)

        self.mdat_input = QLineEdit()
        layout.addRow("MDAT:", self.mdat_input)

        self.submit_button = QPushButton("Hinzufügen")
        self.submit_button.clicked.connect(self.accept)
        layout.addWidget(self.submit_button)

    def get_patient_data(self):
        return {
            "first_name": self.first_name_input.text(),
            "last_name": self.last_name_input.text(),
            "date_of_birth": self.date_of_birth_input.text(),
            "gender": self.gender_input.currentText(),
            "mdat": self.mdat_input.text()
        }