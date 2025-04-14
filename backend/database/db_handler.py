import sqlite3
from config import PATHS

def create_db(name_patient_database: str = "Patientendaten",
                patient_database_path: str = PATHS.DATABASE_PATH_PATIENT,
                pid_database_path: str = PATHS.DATABASE_PATH_PID):
    try:
        with sqlite3.connect(patient_database_path) as conn_patient:
            cursor_patient  = conn_patient.cursor()
    

            cursor_patient.execute(f"""
                CREATE TABLE IF NOT EXISTS {name_patient_database} (
                    patienten_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    date_of_birth TEXT NOT NULL,
                    gender STRING,
                    mdat TEXT,
                    BF BLOB NOT NULL
                )
            """)

            conn_patient.commit()



        with sqlite3.connect(pid_database_path) as conn_pid:
            cursor_pid  =   conn_pid.cursor()


            cursor_pid.execute("""
                CREATE TABLE IF NOT EXISTS pidTable_main (
                    pid_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mdat TEXT NOT NULL,
                    BFS BLOB NOT NULL
                    )
            """)

            conn_pid.commit()
    except sqlite3.Error as e:
        print(f"Fehler beim erstellen der Datenbanekn: {e}")
    finally:
        if conn_patient: conn_patient.close()
        if conn_pid: conn_pid.close()
