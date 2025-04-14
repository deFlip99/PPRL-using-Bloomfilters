from config import init_dir
from backend.database import create_db

def auto_run():
    funcs = [init_dir, create_db]

    for func in funcs:
        func()

