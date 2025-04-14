import sqlite3, os, csv, json
import pandas as pd
from bitarray import bitarray
from datetime import datetime
from backend.bloomfilter import get_bloomfilter, bf_sorenson_dice,bf_extended_similarity, bf_add_salt, bf_convert_blob_to_bf
from backend.data import normalize_date
from config import PATHS, BLOOMFILTER_SETTINGS, GLOBAL_VAL



def db_add_pid_table(table_name: str = None,
                     pid_database_path: str = PATHS.DATABASE_PATH_PID):
    try:
        with sqlite3.connect(pid_database_path) as conn_pid:
            cursor_pid = conn_pid.cursor()

            if table_name is None:
                cursor_pid.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'pidTable_%'")
                existing_tables = cursor_pid.fetchall()
                table_count = len(existing_tables)
                table_name = f"{GLOBAL_VAL.PID_TABLE_PREFIX}{table_count + 1}"

            if table_name == 'pidTable_main':
                print("Ungültiger Name für Table")
                return 0

            cursor_pid.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if cursor_pid.fetchone():
                print("Table mit diesem Namen existiert bereits")
                return 0

            if not table_name.isidentifier():
                print("Ungültiger Tabellenname.")
                return 0

            cursor_pid.execute(f"""
                CREATE TABLE {GLOBAL_VAL.PID_TABLE_PREFIX + table_name}(
                    pid_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mdat TEXT NOT NULL,
                    BFS BLOB NOT NULL)
            """)
    except Exception as e:
        print(f"Fehler beim Erstellen der Tabelle: {e}")

    


def db_delete_pid_table(table_name: str,
                        pid_database_path: str=PATHS.DATABASE_PATH_PID):

    table_name = GLOBAL_VAL.PID_TABLE_PREFIX + table_name

    if table_name == "pidTable_main":
        print(f"Diese Table kann nicht entfernt werden")
        return 0
    try:
        conn_pid = sqlite3.connect(pid_database_path)
        cursor_pid = conn_pid.cursor()

        cursor_pid.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor_pid.fetchone():
            print(f"Table mit Namen '{table_name} existiert nicht")
            return 1

        cursor_pid.execute(f"DROP TABLE {table_name}")
        conn_pid.commit()
    except sqlite3.Error as e:
        print(f"Fehler beim löschen der Tabelle '{table_name}': {e}")
    finally:
        if conn_pid:  
            conn_pid.close()


def db_clear_pid_table(table_name: str,
                        pid_database_path: str = PATHS.DATABASE_PATH_PID):
    table_name = GLOBAL_VAL.PID_TABLE_PREFIX + table_name
    try:
        conn_pid = sqlite3.connectpid_database_path
        cursor_pid = sqlite3.Cursor()

        cursor_pid.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name))
        if not cursor_pid.fetchone():
            print(f"Table mit dem namen '{table_name}' exisitiert nciht")
            conn_pid.close()
            return
        
        cursor_pid.execute(f"DELETE FROM {table_name}")
        conn_pid.commit()

        cursor_pid.execute("VACUUM")
        conn_pid.commit()
    except sqlite3.Error as e:
        print(f"Fehler beim löschen der Tabelle: '{table_name}': {e}")
    finally:
        if conn_pid:
            conn_pid.close()


def db_insert_patient(first_name:str,
                        last_name:str,
                        date_of_birth:str,
                        gender:str="other",
                        mdat:str= None,
                        name_patient_database: str ="Patientendaten",
                        patient_database_path: str = PATHS.DATABASE_PATH_PATIENT):
    date_of_birth = normalize_date(date_of_birth)
    try:
        conn_patient = sqlite3.connect(patient_database_path)
        cursor_patient = conn_patient.cursor()

        bf_list =[
            get_bloomfilter(first_name, BLOOMFILTER_SETTINGS.HASHRUNS_NAME, BLOOMFILTER_SETTINGS.HASH_SEEDS40, BLOOMFILTER_SETTINGS.ARRAY_SIZES["name"], 3, True, "word"),
            get_bloomfilter(last_name, BLOOMFILTER_SETTINGS.HASHRUNS_NAME, BLOOMFILTER_SETTINGS.HASH_SEEDS40, BLOOMFILTER_SETTINGS.ARRAY_SIZES["surname"], 3, True, "word"),
            get_bloomfilter(date_of_birth, BLOOMFILTER_SETTINGS.HASHRUNS_OTHER, BLOOMFILTER_SETTINGS.HASH_SEEDS20, BLOOMFILTER_SETTINGS.ARRAY_SIZES["birthdate"], 2, False, "date"),
            get_bloomfilter(gender, BLOOMFILTER_SETTINGS.HASHRUNS_OTHER, BLOOMFILTER_SETTINGS.HASH_SEEDS20, BLOOMFILTER_SETTINGS.ARRAY_SIZES["gender"], 2, False, "word")
        ]

        bf = bitarray()
        for filter in bf_list: bf.extend(filter)
        
        cursor_patient.execute(f"""
                        INSERT INTO {name_patient_database} (first_name, last_name, date_of_birth, gender, mdat, BF)
                        VALUES (?, ?, ?, ?, ?, ?);
                        """, (first_name, last_name, date_of_birth, gender, mdat, bf.tobytes()))
        conn_patient.commit()

    except Exception as e:
        print(f"Hinzufügen des Patienten Fehlgeschlagen: {e}")
    finally:
        if conn_patient:
            conn_patient.close()


def db_delete_patient(patient_id: int | list[int],
                        name_patient_database: str = "Patientendaten",
                        patient_database_path: str = PATHS.DATABASE_PATH_PATIENT):
    
    if not isinstance(patient_id, list): patient_id = [patient_id]

    try:
        conn_patient = sqlite3.connect(patient_database_path)
        cursor_patient = conn_patient.cursor()

        query = f"DELETE FROM {name_patient_database} WHERE patienten_id IN ({','.join(['?'] * len(patient_id))})"
        cursor_patient.execute(query, patient_id)
        conn_patient.commit()
    except sqlite3.Error as e:
        print(f"Fehler beim Löschen der Patienten: {e}")
    finally:
        if conn_patient:
            conn_patient.close()

def db_export_patient_into_pid(patient_name: tuple[str, str] | list[tuple[str, str]],
                               pid_table_name: str,
                               pid_database_path: str = PATHS.DATABASE_PATH_PID,
                               name_patient_database: str = "Patientendaten",
                               patient_database_path: str = PATHS.DATABASE_PATH_PATIENT):
    if not isinstance(patient_name, list):
        patient_name = [patient_name]

    try:
        with sqlite3.connect(patient_database_path) as conn_patient:
            cursor_patient = conn_patient.cursor()

            query = f"""
                    SELECT mdat, BF FROM {name_patient_database}
                    WHERE (first_name, last_name) IN ({','.join(['(?, ?)'] * len(patient_name))})
                    """
            parameters = [item for name in patient_name for item in name]
            cursor_patient.execute(query, parameters)
            rows = cursor_patient.fetchall()

        if not rows:
            return 0


        with sqlite3.connect(pid_database_path) as conn_pid:
            cursor_pid = conn_pid.cursor()

            cursor_pid.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (GLOBAL_VAL.PID_TABLE_PREFIX + pid_table_name,)
            )
            if not cursor_pid.fetchone():
                db_add_pid_table(pid_table_name)

            query = f"INSERT INTO {GLOBAL_VAL.PID_TABLE_PREFIX + pid_table_name} (mdat, BFS) VALUES (?, ?)"
            cursor_pid.executemany(query, rows)
            conn_pid.commit()

            print(f"{len(rows)} Zeilen erfolgreich in die Tabelle '{pid_table_name}' übertragen.")
            return len(rows)

    except sqlite3.Error as e:
        print(f"Fehler beim Übertragen der Patienten in die PID-Tabelle: {e}")
        return 0



def db_insert_pid(pid_table_name:str,
                random_salt: int = 5,
                salt_list: list[int] = None,
                name_patient_database: str = "Patientendaten",
                patient_database_path: str = PATHS.DATABASE_PATH_PATIENT,
                pid_database_path:str = PATHS.DATABASE_PATH_PID):
    pid_table_name = GLOBAL_VAL.PID_TABLE_PREFIX + pid_table_name

    try:
        with sqlite3.connect(patient_database_path) as conn_patient:
            cursor_patient = conn_patient.cursor()

            cursor_patient.execute(f"SELECT BF, mdat FROM {name_patient_database}")
            rows = cursor_patient.fetchall()

            conn_patient.commit()
            

        with sqlite3.connect(pid_database_path) as conn_pid:
            cursor_pid = conn_pid.cursor()
            
            for bf_bytes, mdat in rows:
                if bf_bytes is None:
                    continue

                bf = bitarray()
                bf.frombytes(bf_bytes)

                bfs = bf_add_salt(bf, random_salt, salt_list)

                cursor_pid.execute(f"INSERT INTO {pid_table_name} (mdat, BFS) VALUES (?, ?)", (mdat, bfs.tobytes()))
            
            conn_pid.commit()
    except sqlite3.Error as e:
        print(f"Fehler beim einlesen der Daten in die PidDB: {e}")
    finally:
        if conn_pid: conn_pid.close()
        if conn_patient:conn_patient.close()


def db_insert_patient_from_file(filename: str, file_path: str = None, file_format: str = 'csv',
                        name_patient_database: str = "Patientendaten",
                        patient_database_path: str = PATHS.DATABASE_PATH_PATIENT,
                        import_path: str = PATHS.IMPORT_DIR):

    if not file_path:
        file_path = os.path.join(import_path, filename)

    if not os.path.exists(file_path):
        print(f"Datei '{filename}' konnte nicht gefunden werden")
        return
    
    try:
        conn_patient = sqlite3.connect(patient_database_path)
        cursor_patient = conn_patient.cursor()

        if file_format.lower() == 'csv':
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if len(row) != 5:
                        print(f"Zeile ist Fehlerhaft: {row}")
                        continue

                    first_name, last_name, date_of_birth, gender, mdat = row
                    mdat = mdat if mdat else None
                    date_of_birth = normalize_date(date_of_birth)

                    bf_list =[
                        get_bloomfilter(first_name, BLOOMFILTER_SETTINGS.HASHRUNS_NAME, BLOOMFILTER_SETTINGS.HASH_SEEDS40, BLOOMFILTER_SETTINGS.ARRAY_SIZES["name"], 3, True, "word"),
                        get_bloomfilter(last_name, BLOOMFILTER_SETTINGS.HASHRUNS_NAME, BLOOMFILTER_SETTINGS.HASH_SEEDS40, BLOOMFILTER_SETTINGS.ARRAY_SIZES["surname"], 3, True, "word"),
                        get_bloomfilter(date_of_birth, BLOOMFILTER_SETTINGS.HASHRUNS_OTHER, BLOOMFILTER_SETTINGS.HASH_SEEDS20, BLOOMFILTER_SETTINGS.ARRAY_SIZES["birthdate"], 2, False, "date"),
                        get_bloomfilter(gender, BLOOMFILTER_SETTINGS.HASHRUNS_OTHER, BLOOMFILTER_SETTINGS.HASH_SEEDS20, BLOOMFILTER_SETTINGS.ARRAY_SIZES["gender"], 2, False, "word")
                    ] 

                    bf = bitarray()
                    for filter in bf_list: bf.extend(filter)
                    cursor_patient.execute(f"""
                            INSERT INTO {name_patient_database} (first_name, last_name, date_of_birth, gender, mdat, BF)
                            VALUES (?, ?, ?, ?, ?, ?);
                            """, (first_name, last_name, date_of_birth, gender, mdat, bf.tobytes()))
                    conn_patient.commit()         


        elif file_format.lower() == 'json':
            with open(file_path, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)
                if not isinstance(data, list):
                    return
                for entry in data:
                    try:
                        first_name = entry['first_name']
                        last_name = entry['last_name']
                        date_of_birth = entry['date_of_birth']
                        gender = entry['gender']
                        mdat = entry.get('mdat', None)
                        bf_list =[
                        get_bloomfilter(first_name, BLOOMFILTER_SETTINGS.HASHRUNS_NAME, BLOOMFILTER_SETTINGS.HASH_SEEDS40, BLOOMFILTER_SETTINGS.ARRAY_SIZES["name"], 3, True, "word"),
                        get_bloomfilter(last_name, BLOOMFILTER_SETTINGS.HASHRUNS_NAME, BLOOMFILTER_SETTINGS.HASH_SEEDS40, BLOOMFILTER_SETTINGS.ARRAY_SIZES["surname"], 3, True, "word"),
                        get_bloomfilter(date_of_birth, BLOOMFILTER_SETTINGS.HASHRUNS_OTHER, BLOOMFILTER_SETTINGS.HASH_SEEDS20, BLOOMFILTER_SETTINGS.ARRAY_SIZES["birthdate"], 2, False, "date"),
                        get_bloomfilter(gender, BLOOMFILTER_SETTINGS.HASHRUNS_OTHER, BLOOMFILTER_SETTINGS.HASH_SEEDS20, BLOOMFILTER_SETTINGS.ARRAY_SIZES["gender"], 2, False, "word")
                        ] 

                        bf = bitarray()
                        for filter in bf_list: bf.extend(filter)
                        cursor_patient.execute(f"""
                                INSERT INTO {name_patient_database} (first_name, last_name, date_of_birth, gender, mdat, BF)
                                VALUES (?, ?, ?, ?, ?, ?);
                                """, (first_name, last_name, date_of_birth, gender, mdat, bf.tobytes()))
                        conn_patient.commit()  
                    except KeyError as ke:
                        print(f"Fehlender Schlüssel {ke} in JSON-Datensatz: {entry}")
                        continue
        else:
            print(f"Dateiformat {file_format} wird nicht unterstürtzt. Verwende 'csv' oder 'json'")
    except Exception as e:
        print(f"Fehler beim Einlesen der Datei: '{filename}'. Fehler: {e}")
    finally:
        if conn_patient:
            conn_patient.close()



#Erhalte alle IDAT ohne mdat aus Patientendaten
def db_get_idat(name_patient_database: str = "Patientendaten",
                patient_database_path: str = PATHS.DATABASE_PATH_PATIENT):
    try:
        conn_patient = sqlite3.connect(patient_database_path)
        cursor_patient = conn_patient.execute(f"SELECT first_name, last_name, date_of_birth, gender, BF FROM {name_patient_database}")
        rows = cursor_patient.fetchall()
        return rows
    except Exception as e:
        print(f"Fehler beim auslesen der idat: {e}")
    finally:
        if conn_patient:   
            conn_patient.close()


#Leert Patientendatenbank
def db_clear_patient_table(name_patient_database: str = "Patientendaten",
                            patient_database_path: str = PATHS.DATABASE_PATH_PATIENT):
    try:
        conn_patient = sqlite3.connect(patient_database_path)
        cursor_patient = conn_patient.cursor()
        cursor_patient.execute(f"DELETE FROM {name_patient_database}")
        conn_patient.commit()
        cursor_patient.execute("VACUUM")  # Speicherplatz freigeben
    except sqlite3.Error as e:
        print(f"Fehler beim Leeren der Tabelle: {e}")
    finally:
        if conn_patient:
            conn_patient.close()


#Datenbank Eintrag basierend auf Vor- und Nachname
def db_lookup_name(patient_name: tuple[str,str] | list[tuple[str,str]], select_output:list[str],
                    name_patient_database: str = "Patientendaten",
                    patient_database_path: str = PATHS.DATABASE_PATH_PATIENT):
    if not isinstance(patient_name, list): patient_name = [patient_name]
    columns = ", ".join(select_output)

    try:
        with sqlite3.connect(patient_database_path) as conn_patient:

            cursor_patient = conn_patient.cursor()

            query = f"""
                        SELECT {columns} FROM {name_patient_database}
                        WHERE (first_name, last_name) IN ({','.join(['(?, ?)'] * len(patient_name))})
                    """
            parameters = [item for name in patient_name for item in name]
            cursor_patient.execute(query, parameters)
            return cursor_patient.fetchall()
    except sqlite3.Error as e:
        print(f"Kein Eintrag gefunden mit den Namen: {patient_name} der Patienten: {e}")
        return []
    finally:
        if conn_patient:
            conn_patient.close()

def db_loopup_id(patient_id: int | list[int], select_output:list[str],
                    name_patient_database: str = "Patientendaten",
                    patient_database_path: str = PATHS.DATABASE_PATH_PATIENT):
    if not isinstance(patient_id, list): patient_id = [patient_id]
    columns = ", ".join(select_output)
    try:
        conn_patient = sqlite3.connect(patient_database_path)
        cursor_patient = conn_patient.cursor()

        query = f"SELECT {columns} FROM {name_patient_database} WHERE patienten_id IN ({','.join(['?']*len(patient_id))})"
        cursor_patient.execute(query, patient_id)
        return cursor_patient.fetchall()
    except sqlite3.Error as e:
        print(f"Kein Eintrag gefunden mit den IDs: {patient_id} der Patienten: {e}")
        return []
    finally:
        if conn_patient:
            conn_patient.close()

#Ähnlichkeit eines BloomFilters zu allen BloomFiltern in der DB mit mindest Ähnlichkeit th
def db_relink_bf(bf:bitarray, th: float,
                    name_patient_database: str = "Patientendaten",
                    patient_database_path: str = PATHS.DATABASE_PATH_PATIENT):
    try:
        conn_patient = sqlite3.connect(patient_database_path)
        cursor = conn_patient.cursor()

        cursor.execute(f"SELECT patienten_id, BF FROM {name_patient_database}")
        rows = cursor.fetchall()

        matching_df = pd.DataFrame(columns=["ID", "Similarity"])

        for row in rows:
            patient_id, db_bf_blob = row

            db_bf = bitarray()
            db_bf.frombytes(db_bf_blob)
            if bf_sorenson_dice(db_bf, bf) > th:
                matching_df.loc[len(matching_df)] = [patient_id, bf_sorenson_dice(db_bf, bf)]
        

        return matching_df
    
    except Exception as e:
        print(f"Fehler beim Zurückführen: {e}")
        return []
    finally:
        if conn_patient:
            conn_patient.close()

def db_extended_relink_bf(bf:bitarray,
                        th: list[float],                       
                        swap: bool = False,
                        out_mode: str = "total",
                        out_notalike: bool = False,
                        name_patient_database: str = "Patientendaten",
                        patient_database_path: str = PATHS.DATABASE_PATH_PATIENT):
    try:
        conn_patient = sqlite3.connect(patient_database_path)
        cursor = conn_patient.cursor()

        cursor.execute(f"SELECT patienten_id, BF FROM {name_patient_database}")
        rows = cursor.fetchall()

        matching_df = pd.DataFrame(columns=["ID", "Rating", "Similarity", "Swaped"])

        for row in rows:
            patient_id, db_bf_blob = row

            db_bf = bitarray()
            db_bf.frombytes(db_bf_blob)

            [similarity, _, rating], swapbool = bf_extended_similarity(..., ..., db_bf, bf, out_mode, th, swap)
            if swapbool:
                swap_text = "Vertauschung von Vorname und Nachname überprüfen"
            else: 
                swap_text = "Keine Vertauschung erkannt"

            if rating in ["strong", "medium", "weak"]:
                matching_df.loc[len(matching_df)] = [patient_id, rating, similarity, swap_text]
            elif rating not in ["strong", "medium", "weak"] and out_notalike:
                matching_df.loc[len(matching_df)] = [patient_id, rating, similarity, swap_text]
        

        return matching_df
    
    except Exception as e:
        print(f"Fehler beim Zurückführen: {e}")
        return []
    finally:
        if conn_patient:
            conn_patient.close()



#Exportiert die ganze pidDB als JSON-Datei oder CSV-Datei
def db_export_pid_to_file(table_name: str, file_format: str = "csv",
                    pid_database_path: str = PATHS.DATABASE_PATH_PID):
    if file_format.lower() not in ["csv", "json"]:
        raise ValueError("Format muss entweder 'csv' oder 'json' sein")
    temp = datetime.now()
    timestamp = temp.strftime("%H-%M_%d-%m")
    filename = f"pid_file_{table_name}_{timestamp}.{file_format.lower()}"

    if file_format.lower() == "json":
        try:
            conn_pid = sqlite3.connect(pid_database_path)
            query = f"SELECT BFS, mdat FROM {GLOBAL_VAL.PID_TABLE_PREFIX + table_name}"
            
            
            df = pd.read_sql_query(query, conn_pid)  
            df['BFS'] = df['BFS'].apply(bf_convert_blob_to_bf)                
            df.rename(columns={'mdat': 'MDAT', 'BFS': 'PID'}, inplace=True)
            filepath = os.path.join(PATHS.EXPORT_DIR, filename)
            
            df.to_json(filepath, orient="records", indent=4, force_ascii=False)

        except Exception as e:
            print(f"Exportieren der PID-Daten fehlgeschlagen: {e}")

        finally:
            if conn_pid:
                conn_pid.close()


    elif file_format.lower() == "csv":
        try:
            conn_pid = sqlite3.connect(pid_database_path)
            query = f"SELECT mdat, BFS FROM {GLOBAL_VAL.PID_TABLE_PREFIX + table_name}"

            df = pd.read_sql_query(query, conn_pid)
            df['BFS'] = df['BFS'].apply(bf_convert_blob_to_bf)
            filepath = os.path.join(PATHS.EXPORT_DIR, filename)

            df.to_csv(filepath, header=["MDAT", "PID"],index=False)

        except Exception as e:
            print(f"Exportieren der PID-Daten fehlgeschlagen: {e}")

        finally:
            if conn_pid:
                conn_pid.close()

    else: raise ValueError("Format muss entweder 'csv' oder 'json' sein")


def db_export_patient_to_file(first_name: str, last_name: str, file_format: str = "csv",
                              patient_database_path: str = PATHS.DATABASE_PATH_PATIENT):
    if file_format.lower() not in ["csv", "json"]:
        raise ValueError("Format muss entweder 'csv' oder 'json' sein")

    try:
        conn_patient = sqlite3.connect(patient_database_path)
        query = f"""
                    SELECT first_name, last_name, BF
                    FROM Patientendaten
                    WHERE first_name = ? AND last_name = ?
                """
        
        df = pd.read_sql_query(query, conn_patient, params=(first_name, last_name))
        
        # BF muss umgewandelt werden, falls nötig (z.B. von BLOB)
        df['BF'] = df['BF'].apply(bf_convert_blob_to_bf)

        temp = datetime.now()
        timestamp = temp.strftime("%H-%M_%d-%m")
        filename = f"patient_{first_name}_{last_name}_{timestamp}.{file_format}"
        filepath = os.path.join(PATHS.EXPORT_DIR, filename)

        if file_format == "json":
            df.to_json(filepath, orient="records", indent=4, force_ascii=False)
        elif file_format == "csv":
            df.to_csv(filepath, header=["Vorname", "Nachname", "BF"], index=False)

        print(f"Datei erfolgreich exportiert: {filepath}")
    
    except Exception as e:
        print(f"Exportieren der Patientendaten fehlgeschlagen: {e}")

    finally:
        if conn_patient:
            conn_patient.close()