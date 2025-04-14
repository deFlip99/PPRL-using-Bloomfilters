from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

class DeleteTableDialog(QDialog):
    def __init__(self, table_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tabelle löschen")
        self.setMinimumSize(300, 150)

        # Layout erstellen
        layout = QVBoxLayout(self)

        # Warntext
        self.label = QLabel(f"Möchten Sie die Tabelle '{table_name}' wirklich löschen?")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # Label für Fehlermeldung
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red; font-weight: bold;")
        self.error_label.setVisible(False)  # Anfangs unsichtbar
        layout.addWidget(self.error_label)

        # Buttons für Bestätigung und Abbruch
        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("Löschen")
        self.confirm_button.clicked.connect(self.handle_confirm)  # Logik für Button
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)  # Abbruch-Button
        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def handle_confirm(self):
        if self.error_label.isVisible():
            return
        self.accept()


    def show_error_message(self, message):
        self.error_label.setText(message)
        self.error_label.setVisible(True)