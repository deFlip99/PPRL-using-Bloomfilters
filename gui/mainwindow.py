from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QListWidget, QStackedWidget,
    QVBoxLayout, QLabel, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from gui.gui_utils import load_stylesheet, create_button
from gui.patient_tab import PatientenTab
from gui.pid_tab import PIDTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PPRL-BloomFilter")
        self.setMinimumSize(600, 400)
        self.setupUI()
        self.setStyleSheet(load_stylesheet("mainwindow.qss"))


    def setupUI(self):
        # Hauptwidget und Grid-Layout
        self.resize(1200, 800)
        mainWidget = QWidget()
        mainLayout = QGridLayout(mainWidget)
        self.setCentralWidget(mainWidget)

        # Linke Sidebar (Navigation)
        self.sidebar = QListWidget()
        self.sidebar.addItems(["Start", "Daten", "Kommunikation", "Datentransfer"])
        self.sidebar.setFixedWidth(180)  # Feste Breite der Sidebar
        self.sidebar.currentRowChanged.connect(self.displayPage)
        mainLayout.addWidget(self.sidebar, 0, 0, 2, 1)

        # StackedWidget für Seiten
        self.stackedWidget = QStackedWidget()
        mainLayout.addWidget(self.stackedWidget, 0, 1, 2, 3)

        # Seiten erstellen
        self.startPage = self.create_start_page()
        self.stackedWidget.addWidget(self.startPage)

        self.dataPage = self.create_data_page()
        self.stackedWidget.addWidget(self.dataPage)

        self.communicationPage = self.create_placeholder_page("Kommunikation")
        self.stackedWidget.addWidget(self.communicationPage)

        self.transferPage = self.create_placeholder_page("Datentransfer")
        self.stackedWidget.addWidget(self.transferPage)

        # Standardseite setzen
        self.sidebar.setCurrentRow(0)

    def create_start_page(self):
        # Startseite
        page = QWidget()
        layout = QVBoxLayout(page)

        welcomeLabel = QLabel("Willkommen zu PPRL mit BloomFiltern")
        welcomeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        font = QFont()
        font.setPointSize(20)
        welcomeLabel.setFont(font)
        layout.addWidget(welcomeLabel)

        # Beispiel-Button
        example_button = create_button(
            "Mehr erfahren",
            "Details über PPRL anzeigen",
            lambda: print("Button 'Mehr erfahren' wurde geklickt!")
        )
        layout.addWidget(example_button)

        return page

    def create_data_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.tabWidget = QTabWidget()
        self.pidTab = PIDTab()
        self.patientenTab = PatientenTab(self.pidTab)
        self.tabWidget.addTab(self.patientenTab, "PatientenDB")
        self.tabWidget.addTab(self.pidTab, "pidDB")

        layout.addWidget(self.tabWidget)
        return page

    def create_placeholder_page(self, label_text):
        # Platzhalterseite für Kommunikation und Datentransfer
        page = QWidget()
        layout = QVBoxLayout(page)

        label = QLabel(f"{label_text} (Platzhalter)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        return page

    def displayPage(self, index):
        self.stackedWidget.setCurrentIndex(index)