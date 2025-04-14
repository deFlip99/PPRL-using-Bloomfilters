from config import PATHS
import os, re, shutil
from werkzeug.utils import secure_filename


def create_upload_folder(folder_name: str):   
    if not 1 < len(folder_name) < 16: raise ValueError("Der Ordnername muss 2 bis 15 Zeichen umfassen")
    if not re.match("^[A-Za-z0-9_-]+$", folder_name): raise ValueError("Der Ordnername darf nur die Zeichen 'a-z', 'A-Z','0-9, sowie '-' und '_' enthalten")
    
    folder_path = os.join(PATHS.UPLOAD_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def upload_file_from_export(target_folder:str, target_file:str):
    target_file = secure_filename(target_file)
    export_file = os.path.join(PATHS.EXPORT_DIR, target_file)

    folder_path = create_upload_folder(target_folder)
    upload_file_path = os.path.join(folder_path, target_file)

    if os.path.exists(export_file):
        shutil.copy(export_file, upload_file_path)
        return upload_file_path
    else: raise FileNotFoundError(f"Die Datei {target_file} existiert nicht oder konnte nicht gefunden werden")
