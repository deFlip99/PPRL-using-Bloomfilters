import csv, random
from datetime import datetime, timedelta
from config import PATHS

# Beispiel-Vornamen und Nachnamen
vornamen = [
    "Alex", "Alexander", "Benjamin", "Carla", "David", "Elena", "Fabian", "Gabriel", "Hanna", "Isabel", "Jonas",
    "Katrin", "Lars", "Miriam", "Noah", "Oliver", "Patrick", "Quentin", "Rebecca", "Samuel", "Tobias",
    "Uwe", "Vanessa", "Walter", "Xenia", "Yannick", "Zoe", "Finn", "Lea", "Nico", "Sophia", 
    "Lena", "Maximilian", "Janina", "Marie", "Pauline", "Emma", "Charlotte", "Johanna", "Leonhard", 
    "Nils", "Jakob", "Hannah", "Mia", "Anna-Lena", "Karl-Heinz", "Maxim", "Lukas", "Eva", "Erik", 
    "Clara", "Theo", "Felix", "Kai", "Timo", "Sophie", "Luisa", "Tom", "Şeyma", "Emre", "Çağıl", "Ömer", 
    "Ümit", "Mehmet", "Fatma", "Aylin", "Efe", "Selin", "Hüseyin", "Büşra", "Ayşegül", "Zeynep", "Murat", 
    "İrem", "Dilara", "Aliye", "Yusuf", "Kadir", "Berkay", "Melek", "Gökhan", "Seda", "Eylül", 
    "Yasemin", "Burak", "Serdar", "Derya", "Çağatay", "Arda", "Vildan", "Gülşah"
]

nachnamen = ["Caputops", "Meyer", "Schmidt", "Becker", "Hoffmann", "Schneider", "Kraus", "Lange", "Schulz", "Peters", "Bauer",
    "Wolf", "Maier", "Kuhn", "Fischer", "Wagner", "Huber", "Keller", "Lorenz", "Berg", "Richter",
    "Sommer", "Braun", "Franke", "Hartmann", "Kruger", "Voigt", "Schuster", "Jung", "Brandt", "Arnold",
    "Müller", "Schäfer", "Böhm", "Köhler", "Fischer", "Schwabe", "Zöller", "Häusler", "Fröhlich", "Hofmann",
    "Vogel", "Stark", "Zimmermann", "Löwe", "Frey", "Schröder", "Blum", "Straub", "Pohl", "Büttner", "Mayer"]

geschlechter = ["männlich", "weiblich", "divers"]
mdats = ["Patient besitzt starken Husten",
        "Patient hat eine Verlestzung an den Wirbeln C2, C3 und C4",
        "Dem Patient wurden Medikamente gegen seine Kopschmerzen verschrieben. Verschriebene Medikamente: Aspirin und Whick Medinight"]


def zufaelliges_geburtsdatum():

    start_date = datetime(1950, 1, 1)
    end_date = datetime(2000, 12, 31)
    
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    geburtsdatum = start_date + timedelta(days=random_days)

    # Zufällig eines der Formate auswählen
    formate = [
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%m-%d-%Y",
        "%d %B %Y",
        "%d.%m.%y",
        "%A, %B %d, %Y",
        "%Y/%m/%d",
        "%m/%d/%Y"
    ]
    
    zufaelliges_format = random.choice(formate)
    
    return geburtsdatum.strftime(zufaelliges_format)

def gen_test_csv(n: int):
# CSV-Datei erstellen und Daten schreiben
    filename = PATHS.INPUT_TESTFILE_PATH
    with open(filename, mode='w', newline='', encoding="utf-8") as datei:
        writer = csv.writer(datei)

        for _ in range(n):
            vorname = random.choice(vornamen)
            nachname = random.choice(nachnamen)
            geburtsdatum = zufaelliges_geburtsdatum()
            geschlecht = random.choice(geschlechter)
            mdat = random.choice(mdats)
            writer.writerow([vorname, nachname, geburtsdatum, geschlecht, mdat])