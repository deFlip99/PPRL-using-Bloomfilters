import sqlite3,datetime, locale, os
from PyQt6.QtWidgets import(QPushButton)
from config import PATHS, GLOBAL_VAL

def load_stylesheet(stylesheet_name: str):
    try:
        # Stelle sicher, dass die style.qss-Datei im gleichen Verzeichnis wie das Skript liegt
        with open(os.path.join(PATHS.STYLESHEETS_DIR, stylesheet_name), "r") as file:
            stylesheet = file.read()
            return stylesheet
    except FileNotFoundError:
        print(f"Fehler beim laden des Stylesheet: {stylesheet_name}")


def fetch_all_patients(database_path: str):
    try:
        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()
            query = "SELECT first_name, last_name, date_of_birth, gender, mdat, BF FROM Patientendaten"
            cursor.execute(query)
            patients = cursor.fetchall()
            return patients
    except sqlite3.Error as e:
        print(f"Fehler beim Abrufen der Patientendaten: {e}")
        return []


def format_date(date_string):
    try:
        locale.setlocale(locale.LC_TIME, "german")

        date_obj = datetime.datetime.strptime(date_string, "%Y%m%d")
        return date_obj.strftime("%d %B %Y")
    except ValueError:
        return date_string
    
def fetch_pid_table_names(database_path: str):
    try:
        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

            tables = [
                row[0].replace(GLOBAL_VAL.PID_TABLE_PREFIX, "")
                for row in cursor.fetchall()
                if row[0] != "sqlite_sequence"
            ]
            return tables
    except sqlite3.Error as e:
        print(f"Fehler beim Abrufen der PID-Tabellen: {e}")
        return []
    
### GUI OBJEKTE###
def create_button(text, tooltip, callback):
    button = QPushButton(text)
    button.setToolTip(tooltip)
    button.clicked.connect(callback)
    return button


