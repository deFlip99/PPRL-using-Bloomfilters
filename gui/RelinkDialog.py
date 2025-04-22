from PyQt6.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem, QGridLayout,QHeaderView
)
from PyQt6.QtCore import Qt
from bitarray import bitarray
from backend.database import (
    db_extended_relink_bf,
    db_lookup_id
)


class RelinkDialog(QDialog):
    def __init__(self, bfs: bytes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Linkage")
        self.setMinimumSize(600, 400)
        
        # BFS aus PIDTab
        self.bfs = bfs
        self.df = None  # DataFrame, den wir anzeigen werden
        
        self.setupUI()
        self.run_relink_logic()

    def setupUI(self):
        # Hauptlayout des Dialogfensters
        main_layout = QGridLayout(self)
        
        # Tabelle zur Darstellung des Ergebnisses
        self.table = QTableWidget()
        main_layout.addWidget(self.table)
        
        # Automatische Anpassung der Spaltenbreiten
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        # Automatische Anpassung der Zeilenhöhen
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        self.setLayout(main_layout)

    def run_relink_logic(self):
        try:
            bf = bitarray()
            bf.frombytes(self.bfs)

            df = db_extended_relink_bf(bf)

            if df.empty:
                print("Keine Übereinstimmung gefunden")
                return

            id_list = df["ID"].tolist()  # Liste aller IDs
            name_tuples = db_lookup_id(id_list, ["first_name", "last_name"])
            if len(name_tuples) != len(id_list):
                print("Warnung: Anzahl der Datensätze passt nicht überein.")
            
            id_map = {}
            for idx, pid in enumerate(id_list):
                if idx < len(name_tuples):
                    vorname, nachname = name_tuples[idx]
                    id_map[pid] = f"{vorname} {nachname}"
                else:
                    id_map[pid] = "Unbekannt"
        
            mapped_series = df["ID"].map(id_map)
            df["ID"] = mapped_series
            df['Similarity'] = df['Similarity'].apply(lambda x: round(x, 3))
            self.df = df
            self.fill_table()
            
        except Exception as e:
            print(f"Fehler in run_relink_logic: {e}")

    def fill_table(self):
        if self.df is None or len(self.df) == 0:
            print("Keine Daten zum Anzeigen.")
            return
        
        rows, cols = self.df.shape
        self.table.setRowCount(rows)
        self.table.setColumnCount(cols)
        
        # Spaltennamen im Header anzeigen
        headers = list(self.df.columns)
        self.table.setHorizontalHeaderLabels(headers)
        
        # Zellen füllen und nicht bearbeitbar machen
        for row_idx in range(rows):
            for col_idx in range(cols):
                val = str(self.df.iat[row_idx, col_idx])
                item = QTableWidgetItem(val)
                
                # Nicht bearbeitbar machen
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                self.table.setItem(row_idx, col_idx, item)

