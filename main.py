from generate_csv import gen_test_csv
from backend.database import db_insert_patient_from_file, db_add_pid_table, db_insert_pid
import sys
from PyQt6.QtWidgets import QApplication
from gui.mainwindow import MainWindow
from backend.auto_exec import auto_run

#Generiere neue Testdaten


def test_run():
    #auto_run()
    #gen_test_csv(50)
    #db_insert_patient_from_file("input.csv")
    #db_add_pid_table("testTable1")
    #db_insert_pid("testTable1")
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

test_run()