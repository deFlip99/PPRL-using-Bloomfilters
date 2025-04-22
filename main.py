from generate_csv import gen_test_csv
import sys
from PyQt6.QtWidgets import QApplication
from gui.mainwindow import MainWindow
from backend.auto_exec import auto_run

#Generiere neue Testdaten


def test_run():
    auto_run()
    gen_test_csv(100)

    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

test_run()