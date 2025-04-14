from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt


class AddTableDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Neues Table erstellen")
        self.setMinimumSize(300, 150)

        # Layout erstellen
        layout = QVBoxLayout(self)

        # Label für die Eingabeaufforderung
        self.label = QLabel("Geben Sie einen Namen für das neue Table ein:")
        layout.addWidget(self.label)

        # Hinweistext für erlaubte Zeichen
        self.rules_label = QLabel("Hinweis: Der Tabellenname darf nur Buchstaben, Zahlen und Unterstriche enthalten. Leerzeichen und Sonderzeichen sind nicht erlaubt.")
        self.rules_label.setWordWrap(True)
        layout.addWidget(self.rules_label)

        # Eingabefeld für den Tabellenname
        self.table_name_input = QLineEdit()
        self.table_name_input.setPlaceholderText("Tabellenname")
        layout.addWidget(self.table_name_input)

        # Label für Fehlernachricht (anfangs leer)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red; font-weight: bold;")  # Roter Text für Fehlermeldung
        self.error_label.setVisible(False)  # Anfangs ausgeblendet
        layout.addWidget(self.error_label)

        # Buttons für Bestätigung und Abbruch
        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("Erstellen")
        self.confirm_button.clicked.connect(self.accept)  # Bestätigungs-Button
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)  # Abbruch-Button
        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def get_table_name(self):
        """Gibt den eingegebenen Tabellennamen zurück."""
        return self.table_name_input.text().strip()

    def show_error_message(self, message):
        """Zeigt eine Fehlermeldung über dem Eingabefeld an."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)