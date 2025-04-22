import sqlite3
from config import PATHS

def create_db(patient_table: str = "Patientendaten",
                patient_db_path: str = PATHS.DATABASE_PATH_PATIENT,
                pid_db_path: str = PATHS.DATABASE_PATH_PID) -> None:
    """
        Create or open two SQLite databases and ensure required tables exist.

        This function will:
            1. Connect to the patient database file and create a table for patient records.
            2. Connect to the PID database file and create a table for PID records.

        Parameters:
            patient_table (str): Name of the patient table to create. Must be a valid SQLite identifier.
            patient_db_path (str): Filesystem path to the patient SQLite database.
            pid_db_path (str): Filesystem path to the PID SQLite database.

        Returns:
            None
    """

    if not patient_table.isidentifier():
        raise ValueError(f"Invalid table name: {patient_table!r}")
    

    patient_sql = f"""
        CREATE TABLE IF NOT EXISTS "{patient_table}" (
            patient_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name    TEXT    NOT NULL,
            last_name     TEXT    NOT NULL,
            date_of_birth TEXT    NOT NULL,
            gender        STRING,
            mdat          TEXT,
            BF       BLOB    NOT NULL
        );
    """

    pid_sql = """
        CREATE TABLE IF NOT EXISTS pidTable_main (
            pid_id INTEGER PRIMARY KEY AUTOINCREMENT,
            mdat   TEXT    NOT NULL,
            bfs    BLOB    NOT NULL
        );
    """

    try:
        with sqlite3.connect(patient_db_path) as conn:
            conn.execute(patient_sql)
            conn.commit()



        with sqlite3.connect(pid_db_path) as conn:
            conn.execute(pid_sql)
            conn.commit()

    except sqlite3.Error as e:
        print(f"Fehler beim erstellen der Datenbanekn: {e}")