import os
##### PATHS ####
class PATHS:
    #general
    BASE_DIR                    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    #database
    DATABASE_DIR                = os.path.join(BASE_DIR, "databases")
    DATABASE_PATH_PATIENT       = os.path.join(DATABASE_DIR, "PatientenDB.db")
    DATABASE_PATH_PID           = os.path.join(DATABASE_DIR, "pidDB.db")

    #local data
    LOCAL_STORAGE_DIR           = os.path.join(BASE_DIR, "local_storage")
    IMPORT_DIR                  = os.path.join(LOCAL_STORAGE_DIR, "import")
    EXPORT_DIR                  = os.path.join(LOCAL_STORAGE_DIR, "export")
    RECEIVED_DIR                = os.path.join(LOCAL_STORAGE_DIR, "received")
    UPLOAD_DIR                  = os.path.join(LOCAL_STORAGE_DIR, "upload")

    INPUT_TESTFILE_PATH         = os.path.join(IMPORT_DIR, "input.csv")
    EXPORT_TESTFILE_PATH        = os.path.join(EXPORT_DIR, "export_placeholder.txt")

    #gui
    GUI_DIR                     = os.path.join(BASE_DIR, "gui")
    STYLESHEETS_DIR             = os.path.join(GUI_DIR, "stylesheets")



def init_dir():
    for directory in [PATHS.DATABASE_DIR, 
                        PATHS.LOCAL_STORAGE_DIR, 
                        PATHS.IMPORT_DIR, 
                        PATHS.EXPORT_DIR, 
                        PATHS.RECEIVED_DIR,
                        PATHS.UPLOAD_DIR]:
        os.makedirs(directory, exist_ok=True)

def ini_placeholder():
    temp = zip(["import.txt", "export.txt", "received.txt"],
                [PATHS.IMPORT_DIR,PATHS.EXPORT_DIR,PATHS.RECEIVED_DIR])
    for (filename, dir) in temp:
        try:
            filename = os.path.join(dir, filename)
            with open(filename, 'w') as file:
                pass  
        except Exception as e:
            print(f"Fehler beim erstellender Datei: {e}")

