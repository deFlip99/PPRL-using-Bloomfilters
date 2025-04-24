import sqlite3, os, csv, json, re
import pandas as pd
from bitarray import bitarray
from datetime import datetime
from backend.bloomfilter import get_bloomfilter, bf_sorenson_dice,bf_extended_similarity, bf_add_salt, bf_convert_bytes_to_01
from backend.data import normalize_date
from config import PATHS, BLOOMFILTER_SETTINGS, GLOBAL_VAL
from sqlite3 import Error as SQLError
from pathlib import Path

def db_add_pid_table(
        table_name: str | None = None,
        pid_db_path: str = PATHS.DATABASE_PATH_PID
) -> str:
    """
        Create a new PID table in the specified SQLite database.

        Parameters:
            table_name (str | None):    If provided, used as the new table’s name.
                                        If None, the function auto‑increments based on existing tables.
            pid_db_path (str):          Path to the PID SQLite database file.

        Returns:
            str                         The full name of the newly created table.
    """

    prefix = GLOBAL_VAL.PID_TABLE_PREFIX

    
    with sqlite3.connect(pid_db_path) as conn:
        cursor = conn.cursor()

        if table_name is None:
            # Find all existing pid tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?",
                (f"{prefix}%",)
            )
            existing = [row[0] for row in cursor.fetchall()]


            nums = [
                int(m.group(1))
                for name in existing
                if (m := re.match(re.escape(prefix) + r"(\d+)$", name))
            ]
            next_num = max(nums, default=0) + 1
            table_name = f"{prefix}{next_num}"
        else:
            table_name = table_name if table_name.startswith(prefix) else f"{prefix}{table_name}"


        if table_name.lower() == f"{prefix}main".lower():
            raise ValueError(f"'{prefix}main' is reserved and cannot be used.")

        #Validate as a Python/SQlite identifier
        if not table_name.isidentifier():
            raise ValueError(f"Invalid table name: {table_name!r}")

        #Ensure it doesn’t already exist
        cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if cursor.fetchone():
            raise ValueError(f"Table {table_name!r} already exists.")

        #Create the new table
        create_sql = f"""
        CREATE TABLE "{table_name}" (
            pid_id INTEGER PRIMARY KEY AUTOINCREMENT,
            mdat   TEXT    NOT NULL,
            bfs    BLOB    NOT NULL
        );
        """
        cursor.execute(create_sql)
        conn.commit()

    return table_name


def db_delete_pid_table(table_name: str,
                        pid_db_path: str=PATHS.DATABASE_PATH_PID) -> int | None:
    """
        Delete a PID table from the given SQLite database.

        Parameters:
            table_name (str):       Suffix of the PID table to delete.
            pid_db_path (str):      Path to the PID SQLite database.

        Returns:
            int                     0 if deletion is not permitted (main table) or an error occurs,
                                    1 if the specified table does not exist,
                                    None on successful deletion.
    """
    full_name = GLOBAL_VAL.PID_TABLE_PREFIX + table_name

    # Prevent deleting the main table
    if full_name == "pidTable_main":
        print("This table cannot be removed")
        return 0

    try:
        conn_pid = sqlite3.connect(pid_db_path)
        cursor_pid = conn_pid.cursor()

        # Check for existence
        cursor_pid.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (full_name,)
        )
        if not cursor_pid.fetchone():
            print(f"Table with name '{full_name}' does not exist")
            return 1

        # Drop the table
        cursor_pid.execute(f"DROP TABLE {full_name}")
        conn_pid.commit()

    except sqlite3.Error as e:
        print(f"Error deleting table '{full_name}': {e}")
        return 0

    finally:
        conn_pid.close()



def db_insert_patient(
    first_name: str,
    last_name: str,
    date_of_birth: str,
    gender: str = "other",
    mdat: str | None = None,
    patient_table: str = "Patientendaten",
    patient_db_path: str = PATHS.DATABASE_PATH_PATIENT
) -> int | None:
    """
    Insert a new patient into the database, computing and storing a Bloom filter.

    Parameters:
        first_name (str):       Patient's first name.
        last_name (str):        Patient's last name.
        date_of_birth (str):    Date of birth.
        gender (str):           Gender identifier (default: "other").
        mdat (str | None):      Optional mmedicaldata.
        patient_table (str):    Name of the patient table.
        patient_db_path (str):  Path to the patient database.

    Returns:
        Optional[int]: The new patient's row ID on success, or None on failure.
    """


    # Normalize date and validate table name
    dob = normalize_date(date_of_birth)
    if not patient_table.isidentifier():
        raise ValueError(f"Invalid table name: {patient_table!r}")

    # Build and combine the Bloom filters
    bf_list = [
        get_bloomfilter(first_name,
                        BLOOMFILTER_SETTINGS.HASHRUNS_NAME,
                        BLOOMFILTER_SETTINGS.HASH_SEEDS40,
                        BLOOMFILTER_SETTINGS.ARRAY_SIZES["name"],
                        "word"),
        get_bloomfilter(last_name,
                        BLOOMFILTER_SETTINGS.HASHRUNS_NAME,
                        BLOOMFILTER_SETTINGS.HASH_SEEDS40,
                        BLOOMFILTER_SETTINGS.ARRAY_SIZES["name"],
                        "word"),
        get_bloomfilter(dob,
                        BLOOMFILTER_SETTINGS.HASHRUNS_OTHER,
                        BLOOMFILTER_SETTINGS.HASH_SEEDS20,
                        BLOOMFILTER_SETTINGS.ARRAY_SIZES["other"],
                        "date"),
        get_bloomfilter(gender,
                        BLOOMFILTER_SETTINGS.HASHRUNS_OTHER,
                        BLOOMFILTER_SETTINGS.HASH_SEEDS20,
                        BLOOMFILTER_SETTINGS.ARRAY_SIZES["other"],
                        "word"),
    ]
    combined_bf = bitarray()
    for ba in bf_list:
        combined_bf.extend(ba)
    bf_bytes = combined_bf.tobytes()

    # Prepare and execute the INSERT statement
    query = (
        f'INSERT INTO "{patient_table}" '
        '(first_name, last_name, date_of_birth, gender, mdat, BF) '
        'VALUES (?, ?, ?, ?, ?, ?);'
    )

    try:
        with sqlite3.connect(patient_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query,(first_name, last_name, dob, gender, mdat, bf_bytes))
            return cursor.lastrowid
    except SQLError as e:
        print(f"Failed to insert patient: {e}")
        return None


def db_delete_patient(
    patient_id: int | list[int],
    patient_table: str = "Patientendaten",
    patient_db_path: str = PATHS.DATABASE_PATH_PATIENT
) -> int:
    
    """
    Delete one or more patients by ID from the specified database table.

    Parameters:
        patient_id (int | list[int]):   Single ID or list of IDs to delete.
        patient_table (str):            Name of the patient table.
        patient_db_path (str):          Path ath to the patient database.

    Returns:
        int:                            Number of rows deleted.
    """

    ids = [patient_id] if isinstance(patient_id, int) else patient_id

    # Validates table name
    if not patient_table.isidentifier():
        raise ValueError(f"Invalid table name: {patient_table!r}")

    query = f'DELETE FROM "{patient_table}" WHERE patient_id IN ({",".join("?" for _ in ids)})'

    try:
        with sqlite3.connect(patient_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, ids)
            return cursor.rowcount
    except sqlite3.Error as e:
        print(f"Failed to delete patients: {e}")
        return 0


def db_export_patient_into_pid(
    patient_names: tuple[str, str] | list[tuple[str, str]],
    pid_table_name: str,
    pid_db_path: str = PATHS.DATABASE_PATH_PID,
    patient_table: str = "Patientendaten",
    patient_db_path: str = PATHS.DATABASE_PATH_PATIENT
) -> int:
    
    """
    Export mdat and BF values for given patient names into a PID table.

    Parameters:
        patient_names (tuple[str, str] | list[tuple[str, str]]):    (first_name, last_name) tuple or list of such tuples to export.
        pid_table_name (str):                                       Name of the PID table.
        pid_db_path (str):                                          Path to the PID database.
        patient_table (str):                                        Name of the patient table.
        patient_db_path (str):                                      Path to the patient database.

    Returns:
        int: The number of rows exported (0 if none or on error).
    """

    names = patient_names if isinstance(patient_names, list) else [patient_names]

    # Validate table name
    if not patient_table.isidentifier():
        raise ValueError(f"Invalid patient table name: {patient_table}")

    pid_table = pid_table_name if pid_table_name.startswith(GLOBAL_VAL.PID_TABLE_PREFIX) else GLOBAL_VAL.PID_TABLE_PREFIX + pid_table_name
    if not pid_table.isidentifier():
        raise ValueError(f"Invalid PID table name: {pid_table}")

    try:
        query = (f'''
            SELECT mdat, BF FROM "{patient_table}" 
            WHERE (first_name, last_name) IN ({", ".join(["(?,?)"] * len(names))})
            '''
        )
        params = [item for name in names for item in name]
        with sqlite3.connect(patient_db_path) as conn_pat:
            cursor_pat = conn_pat.cursor()
            cursor_pat.execute(query, params)
            rows = cursor_pat.fetchall()

        if not rows:
            return 0

        with sqlite3.connect(pid_db_path) as conn_pid:
            cur_pid = conn_pid.cursor()
            cur_pid.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (pid_table,)
            )
            if not cur_pid.fetchone():
                db_add_pid_table(pid_table_name)

            # Insert into PID table
            insert_query = f'INSERT INTO "{pid_table}" (mdat, BFS) VALUES (?, ?)'
            cur_pid.executemany(insert_query, rows)
            conn_pid.commit()

        return len(rows)
    except sqlite3.Error as e:
        print(f"Error exporting patients to PID table '{pid_table}': {e}")
        return 0


def db_insert_pid(
    pid_table_name: str,
    salt_amount: int = 5,
    salt_fixed: list[int] | None = None,
    patient_table: str = "Patientendaten",
    patient_db_path: str = PATHS.DATABASE_PATH_PATIENT,
    pid_db_path: str = PATHS.DATABASE_PATH_PID
) -> int:
    
    """
    Read Bloom filters from the patient table, add salt, and insert into a PID table.

    Parameters:
        pid_table_name (str):           PID table name.
        salt_amount (int):              Number of random bits set to 1 in each Bloom filter.
        salt_fixed (list[int]|None):    Given bit indices set to 1; prefered over salt_amount.
        patient_table (str):            Name of the patient table.
        patient_db_path (str):          Path to the patient database.
        pid_db_path (str):              Path to the PID database.

    Returns:
        int: The number of rows successfully inserted into the PID table.
    """

    pid_table = pid_table_name if pid_table_name.startswith(GLOBAL_VAL.PID_TABLE_PREFIX) else GLOBAL_VAL.PID_TABLE_PREFIX + pid_table_name

    # Validate identifiers
    for name in (patient_table, pid_table):
        if not name.isidentifier():
            raise ValueError(f"Invalid table name: {name}")

    inserted = 0
    try:
        # Fetch Bloom filters and medical data from patient DB
        query = f'SELECT BF, mdat FROM "{patient_table}"'
        with sqlite3.connect(patient_db_path) as conn_pat:
            cursor_pat = conn_pat.cursor()
            cursor_pat.execute(query)
            rows = cursor_pat.fetchall()

        if not rows:
            return 0

        # Insert salted filters into PID DB
        with sqlite3.connect(pid_db_path) as conn_pid:
            cur_pid = conn_pid.cursor()
            query = f'INSERT INTO "{pid_table}" (mdat, BFS) VALUES (?, ?)'

            for bf_bytes, mdat in rows:
                if bf_bytes is None:
                    continue
                bf = bitarray()
                bf.frombytes(bf_bytes)
                salted = bf_add_salt(bf, salt_amount, salt_fixed)
                cur_pid.execute(query, (mdat, salted.tobytes()))
                inserted += 1

            conn_pid.commit()

        return inserted

    except sqlite3.Error as e:
        print(f"Error inserting into PID table '{pid_table}': {e}")
        return inserted


def db_insert_patient_record_helper(row,
                                    sql_cursor: sqlite3.Cursor,
                                    patient_table:str = "Patientendaten"
                                    ):
    fname, lname, dob, gender, mdat = row
    bf_list = [
        get_bloomfilter(fname, BLOOMFILTER_SETTINGS.HASHRUNS_NAME, BLOOMFILTER_SETTINGS.HASH_SEEDS40, BLOOMFILTER_SETTINGS.ARRAY_SIZES['name'], 'word'),
        get_bloomfilter(lname, BLOOMFILTER_SETTINGS.HASHRUNS_NAME, BLOOMFILTER_SETTINGS.HASH_SEEDS40, BLOOMFILTER_SETTINGS.ARRAY_SIZES['name'], 'word'),
        get_bloomfilter(dob, BLOOMFILTER_SETTINGS.HASHRUNS_OTHER, BLOOMFILTER_SETTINGS.HASH_SEEDS20, BLOOMFILTER_SETTINGS.ARRAY_SIZES['other'], 'date'),
        get_bloomfilter(gender, BLOOMFILTER_SETTINGS.HASHRUNS_OTHER, BLOOMFILTER_SETTINGS.HASH_SEEDS20, BLOOMFILTER_SETTINGS.ARRAY_SIZES['other'], 'word'),
    ]
    bf = bitarray()
    for b in bf_list:
        bf.extend(b)
    sql_cursor.execute(
        f"INSERT INTO {patient_table} (first_name, last_name, date_of_birth, gender, mdat, BF) VALUES (?, ?, ?, ?, ?, ?)",
        (fname, lname, dob, gender, mdat or None, bf.tobytes())
    )


def db_insert_patient_from_file(
    filename: str,
    file_path: str | None = None,
    file_format: str = 'csv',
    patient_table: str = 'Patientendaten',
    patient_db_path: str = PATHS.DATABASE_PATH_PATIENT,
    import_dir: str = PATHS.IMPORT_DIR
) -> int:
    """
    Bulk import patients from a CSV or JSON file into the patient database.

    Parameters:
        filename (str):          Name of the file to import.
        file_path (str | None):  Full path to the file; overrides import_dir if provided.
        file_format (str):       file format of the file to import.
        patient_table (str):     Name of the patient table.
        patient_db_path (str):   Path to the patient database.
        import_dir (str):        Directory to look up the file if file_path is None.

    Returns:
        int: Number of rows successfully inserted.
    """
    # Resolve file path
    file_path = Path(file_path) if file_path else Path(import_dir) / filename
    if not file_path.exists():
        print(f"File '{file_path}' not found.")
        return 0

    if not os.path.exists(file_path):
        print(f"File '{filename}' could not be found")
        return
    
    if not patient_table.isidentifier():
        raise ValueError(f"Invalid table name: {patient_table!r}")

    inserted = 0
    file_format = file_format.lower()
    try:
        with sqlite3.connect(patient_db_path) as conn:
            cursor = conn.cursor()

            if file_format == 'csv':
                with file_path.open(newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) != 5:
                            print(f"Skipping row: {row}")
                            continue
                        db_insert_patient_record_helper(row, cursor)
                        inserted += 1

            elif file_format == 'json':
                data = json.loads(file_path.read_text(encoding='utf-8'))
                if not isinstance(data, list):
                    raise ValueError("JSON import requires a list of records.")
                for entry in data:
                    try:
                        row = [
                            entry['first_name'],
                            entry['last_name'],
                            entry['date_of_birth'],
                            entry['gender'],
                            entry.get('mdat', None)
                        ]
                        db_insert_patient_record_helper(row, cursor)
                        inserted += 1
                    except KeyError as ke:
                        print(f"Missing key {ke} in record: {entry}")
                        continue

            else:
                raise ValueError(f"Unsupported format: {file_format}. Use 'csv' or 'json'.")

            conn.commit()
    except sqlite3.Error as e:
        print(f"Error importing file '{filename}': {e}")
    return inserted



#Helper function not in use so far returns all IDAT without mdat
def db_get_idat(patient_table: str = "Patientendaten",
                patient_db_path: str = PATHS.DATABASE_PATH_PATIENT):
    try:
        conn_patient = sqlite3.connect(patient_db_path)
        cursor_patient = conn_patient.execute(f"SELECT first_name, last_name, date_of_birth, gender, BF FROM {patient_table}")
        rows = cursor_patient.fetchall()
        return rows
    except Exception as e:
        print(f"Fehler beim auslesen der idat: {e}")
    finally:
        if conn_patient:   
            conn_patient.close()



def db_clear_pid_table(
    table_name: str,
    pid_db_path: str = PATHS.DATABASE_PATH_PID
) -> int:
    
    """
    Delete all rows from the specified PID table and reclaim space via VACUUM.

    Parameters:
        table_name (str):       Name of the PID table to clear.
        pid_db_path (str):      Path to the PID database.

    Returns:
        int: Number of rows deleted, or 0 if the table doesn't exist or on error.
    """

    # Compute full table name with prefix
    table_name = table_name if table_name.startswith(GLOBAL_VAL.PID_TABLE_PREFIX) else GLOBAL_VAL.PID_TABLE_PREFIX + table_name

    # Validate table name
    if not table_name.isidentifier():
        raise ValueError(f"Invalid table name: {table_name!r}")

    try:
        with sqlite3.connect(pid_db_path) as conn:
            cursor = conn.cursor()

            # Check existence
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            if not cursor.fetchone():
                print(f"Table '{table_name}' does not exist.")
                return 0

            # Delete all data
            cursor.execute(f'DELETE FROM {table_name}')
            deleted = cursor.rowcount
            conn.commit()
            # Reclaim database space
            cursor.execute("VACUUM")
            conn.commit()

            return deleted

    except sqlite3.Error as e:
        print(f"Error clearing table '{table_name}': {e}")
        return 0



#Datenbank Eintrag basierend auf Vor- und Nachname
def db_lookup_name(
    patient_names: tuple[str, str] | list[tuple[str, str]],
    select_columns: list[str],
    patient_table: str = "Patientendaten",
    patient_db_path: str = PATHS.DATABASE_PATH_PATIENT
) -> list[tuple]:
    
    """
    Retrieve specified columns for patients identified by first and last names.

    Parameters:
        patient_names (tuple[str, str] | list[tuple[str, str]]):
            Siingle or list of (first_name, last_name) tuples to search for.
        select_columns (list[str]):
            List of valid column names to retrieve from the table.
        patient_table (str):
            Name of the patient table.
        patient_db_path (str):
            Path to the patient database.

    Returns:
        list[tuple]: A list of tuples representing the requested columns for matching patients.
    """

    # Normalize to list
    names = patient_names if isinstance(patient_names, list) else [patient_names]

    # Validate table name
    if not patient_table.isidentifier():
        raise ValueError(f"Invalid table name: {patient_table!r}")

    # Validate and quote column names
    quoted_cols = []
    for col in select_columns:
        if not col.isidentifier():
            raise ValueError(f"Invalid column name: {col!r}")
        quoted_cols.append(f'"{col}"')
    columns_str = ", ".join(quoted_cols)


    params = [item for name in names for item in name]

    query = (f'''
            SELECT {columns_str} FROM "{patient_table}" 
            WHERE (first_name, last_name) IN ({", ".join(["(?, ?)" for _ in names])})
        '''
    )

    try:
        with sqlite3.connect(patient_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error looking up patients {names}: {e}")
        return []
    

def db_lookup_id(
    patient_ids: int | list[int],
    select_columns: list[str],
    patient_table: str = "Patientendaten",
    patient_db_path: str = PATHS.DATABASE_PATH_PATIENT
) -> list[tuple]:
    """
    Retrieve specified columns for patients identified by their IDs.

    Parameters:
        patient_ids (int | list[int]):  Single ID or list of IDs to search for.
        select_columns (list[str]):     List of valid column names to retrieve.
        patient_table (str):            Name of the patient table (must be a valid identifier).
        patient_db_path (str):          Filesystem path to the patient SQLite database.

    Returns:
        list[tuple]: Tuples of requested column values for matching patient IDs, or an empty list on error.
    """
    # Normalize IDs to a list
    ids = [patient_ids] if isinstance(patient_ids, int) else patient_ids

    # Validate table name
    if not patient_table.isidentifier():
        raise ValueError(f"Invalid table name: {patient_table!r}")

    # Validate column names
    quoted_cols = []
    for col in select_columns:
        if not col.isidentifier():
            raise ValueError(f"Invalid column name: {col!r}")
        quoted_cols.append(f'"{col}"')
    columns_str = ", ".join(quoted_cols)

    query = (
        f'SELECT {columns_str} FROM "{patient_table}" '
        f'WHERE patient_id IN ({", ".join(["?"] * len(ids))})'
    )

    try:
        with sqlite3.connect(patient_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, ids)
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error looking up patient IDs {ids}: {e}")
        return []

#Einfache Relink variante bisher nicht verwendet
def db_relink_bf(bf:bitarray, th: float,
                    patient_table: str = "Patientendaten",
                    patient_db_path: str = PATHS.DATABASE_PATH_PATIENT):
    try:
        conn_patient = sqlite3.connect(patient_db_path)
        cursor = conn_patient.cursor()

        cursor.execute(f"SELECT patienten_id, BF FROM {patient_table}")
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


def db_extended_relink_bf(
    bf: bitarray,
    thresholds: list[float] = GLOBAL_VAL.RECORD_LINKAGE_TH,
    swap: bool = False,
    out_mode: str = "total",
    include_notalike: bool = False,
    patient_table: str = "Patientendaten",
    patient_db_path: str = PATHS.DATABASE_PATH_PATIENT
) -> pd.DataFrame:
    
    """
    Compare a given Bloom filter against all stored patient filters and
    compute extended similarity.

    Parameters:
        bf (bitarray):
            The target Bloom filter to relink.
        thresholds (list[float]):
            Three similarity thresholds for rating categories.
        swap (bool):
            If True, allow first/last name swap during comparison.
        out_mode (str):
            Similarity output mode passed to bf_extended_similarity.
        include_notalike (bool):
            If True, include records rated below 'weak'.
        patient_table (str):
            Name of the patient table.
        patient_db_path (str):
            Path to the patient database.

    Returns:
        pd.DataFrame: Rows with columns ['ID', 'Rating', 'Similarity', 'Swapped'], one per matching patient.
    """

    # Validate identifier
    if not patient_table.isidentifier():
        raise ValueError(f"Invalid table name: {patient_table!r}")

    records = []
    try:
        with sqlite3.connect(patient_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'SELECT patient_id, BF FROM "{patient_table}"')
            rows = cursor.fetchall()

        for patient_id, bf_blob in rows:
            db_bf = bitarray()
            db_bf.frombytes(bf_blob)

            (similarity, _, rating), did_swap = bf_extended_similarity(
                db_bf,
                bf,
                [
                    BLOOMFILTER_SETTINGS.ARRAY_SIZES["name"],
                    BLOOMFILTER_SETTINGS.ARRAY_SIZES["name"],
                    BLOOMFILTER_SETTINGS.ARRAY_SIZES["other"],
                    BLOOMFILTER_SETTINGS.ARRAY_SIZES["other"]
                ],
                ["first name", "last name", "birthdate", "gender"],
                out_mode,
                thresholds,
                swap
            )
            swap_text = (
                "Swap detected (first/last name)" if did_swap
                else "No swap"
            )

            if rating in ["strong", "medium", "weak"] or did_swap or include_notalike:
                records.append({
                    "ID": patient_id,
                    "Rating": rating,
                    "Similarity": similarity,
                    "Swapped": swap_text
                })

        return pd.DataFrame(records, columns=["ID", "Rating", "Similarity", "Swapped"])

    except sqlite3.Error as e:
        print(f"Database error during relink: {e}")
        return pd.DataFrame(columns=["ID", "Rating", "Similarity", "Swapped"])


def db_export_pid_to_file(
    table_name: str,
    file_format: str = "csv",
    pid_db_path: str = PATHS.DATABASE_PATH_PID,
    export_dir: str = PATHS.EXPORT_DIR
) -> Path:
    
    """
    Export PID table data to a CSV or JSON file, converting Bloom filters to 0/1 strings.

    Parameters:
        table_name (str):   Name of the PID table.
        file_format (str):  Fileformat of the file to export; 'csv' or 'json'.
        pid_db_path (str):  Path to the PID database.
        export_dir (str):   Directory where the file will be exported to.

    Returns:
        pathlib.Path:       Path to the exported file.
    """

    # Normalize and validate file format
    format = file_format.lower()
    if format not in ("csv", "json"):
        raise ValueError("Format must be 'csv' or 'json'.")

    # Validate table name
    table_name = table_name if table_name.startswith(GLOBAL_VAL.PID_TABLE_PREFIX) else GLOBAL_VAL.PID_TABLE_PREFIX + table_name
    if not table_name.isidentifier():
        raise ValueError(f"Invalid table name: {table_name!r}")

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pid_{table_name}_{timestamp}.{format}"
    export_path = Path(export_dir) / filename

    query = f'SELECT mdat AS MDAT, BFS FROM "{table_name}"'
    try:
        with sqlite3.connect(pid_db_path) as conn:
            df = pd.read_sql_query(query, conn)
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Database error reading table '{table_name}': {e}")

    # Convert Bloom filter bytes to 0/1 strings
    df['PID'] = df['BFS'].apply(bf_convert_bytes_to_01)
    df.drop(columns=['BFS'], inplace=True)

    # Export to file
    try:
        export_path.parent.mkdir(parents=True, exist_ok=True)
        if format == 'csv':
            df.to_csv(export_path, index=False)
        else:
            df.to_json(export_path, orient='records', indent=2, force_ascii=False)
    except Exception as e:
        raise IOError(f"Failed to write {format.upper()} file: {e}")

    return export_path


def db_export_patient_to_file(
    first_name: str | list[str],
    last_name: str | list[str],
    file_format: str = 'csv',
    patient_table: str = 'Patientendaten',
    patient_db_path: str = PATHS.DATABASE_PATH_PATIENT,
    export_dir: str = PATHS.EXPORT_DIR
) -> Path:
    """
    Export patient Bloomfilters to a CSV or JSON file by name lookup.

    Parameters:
        first_name (str | list[str]):   Single first name or list of first names.
        last_name (str | list[str]):    Single last name or list of last names.
        file_format (str):              File format of the exported file; 'csv' or 'json'.
        patient_table (str):            Name of the patient table in the database.
        patient_db_path (str):          Path to the patient database.
        export_dir (str):               Directory where the file will be exported to.

    Returns:
        pathlib.Path:                   Path to the exported file.
    """

    # Validate export format
    fmt = file_format.lower()
    if fmt not in ('csv', 'json'):
        raise ValueError("file_format must be 'csv' or 'json'.")


    # Normalize and validate name inputs
    single = isinstance(first_name, str) and isinstance(last_name, str)
    multiple = isinstance(first_name, list) and isinstance(last_name, list)
    if not (single or multiple):
        raise TypeError('first_name and last_name must both be str or both be list[str]')
    if multiple and len(first_name) != len(last_name):
        raise ValueError('first_name and last_name lists must have the same length')

    # Build SQL query and params
    if single:
        query = (f'''
            SELECT first_name AS FirstName, last_name AS LastName, BF FROM '{patient_table}' 
            WHERE first_name = ? AND last_name = ?
        '''
        )
        params = (first_name, last_name)
        base_filename = f"patient_{first_name}_{last_name}"
    else:
        
        query = (f'''
            SELECT first_name AS FirstName, last_name AS LastName, BF FROM '{patient_table}' 
            WHERE (first_name, last_name) IN ({', '.join(['(?, ?)'] * len(first_name))})'''
        )
        params = [val for pair in zip(first_name, last_name) for val in pair]
        base_filename = f"patients_{len(first_name)}"

    # Load data
    with sqlite3.connect(patient_db_path) as conn:
        df = pd.read_sql_query(query, conn, params=params)

    df['BF'] = df['BF'].apply(bf_convert_bytes_to_01)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{base_filename}_{timestamp}.{fmt}"
    export_path = Path(export_dir) / filename
    export_path.parent.mkdir(parents=True, exist_ok=True)

    # Export file
    if fmt == 'csv':
        df.to_csv(export_path, index=False)
    else:
        df.to_json(export_path, orient='records', indent=2, force_ascii=False)

    return export_path

