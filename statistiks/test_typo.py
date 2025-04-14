import os, sys,csv, random
from statistics import mean, median
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bitarray import bitarray
from test_csv import generate_csv
from statistiks.test_settings import *
from backend.bloomfilter import bf_extended_similarity, get_bloomfilter
from temp import achter



typo_testdata = [
    ("Lukas", "Meier", "1990-05-12", "Männlich"),
    ("Anna", "Fischer", "23.09.1985", "Weiblich"),
    ("Julian", "Schmitt", "08/07/1998", "Männlich"),
    ("Laura", "Becker", "1992/03/17", "Weiblich"),
    ("Robin", "Keller", "2001/12/30", "Divers"),
    ("Maximilian", "Van Bürgerstadt", "2001-12-30", "Divers"),
    ("王", "伟", "1993/06/14", "Männlich"),
    ("李", "娜", "05/11/1997", "Weiblich"),
    ("أحمد", "علي", "20/04/1989", "Männlich"),
    ("فاطمة", "حسن", "15.08.1995", "Weiblich"),
    # ("Çağlar", "Yıldız", "28/02/1991", "Männlich"),
    # ("Elif", "Şahin", "10/10/1996", "Weiblich"),
    # ("Émile", "Dubois", "1984-07-22", "Männlich"),
    # ("Chloé", "Lefèvre", "1999/05/18", "Weiblich"),
    # ("Mäx", "Römer", "1985-03-12", "Männlich"),
    # ("Jürgen", "Müller", "1992/11/23", "Männlich"),
    # ("Käthe", "Schneider", "05.06.1978", "Weiblich"),
    # ("Björk", "Lund", "1994/09/18", "Weiblich"),
    # ("Ömer", "Yılmaz", "30/07/1982", "Männlich"),
    # ("Maximilian", "Schulz-Braun", "2000/12/15", "Divers"),
    # ("Anna-Lena", "Schmidt", "09.04.1998", "Weiblich"),
    ("Marie-Claire", "Heinrich", "20.02.1986", "Weiblich"),
    ("Karl-Heinz", "Schmidt", "05/09/1973", "Männlich"),
    ("John-Paul", "Harris", "1991/07/22", "Männlich")
]


def run_typo_test(first_name, last_name, date_of_birth, gender,
                  hash_runs_fname,
                  hash_runs_lname,
                  hash_runs_dob,
                  hash_runs_gen,
                  fname_asize,
                  lname_asize,
                  dob_asize,
                  gender_asize, file):


    read_filename   = first_name[:2]+last_name[:2]
    samplecount     = 250

    first_name      = first_name[:16]
    array_sizes     = [fname_asize ,fname_asize,dob_asize,gender_asize]

    #generate_csv(first_name, last_name, date_of_birth, gender, samplecount, filename = read_filename)
    write_filename  =   f"statistiks/typo_{read_filename}_{file}_result.txt"
    read_filename   =   f"statistiks/typo_{read_filename}.csv"
    bf_list = [
                get_bloomfilter(first_name, hash_runs_fname, HASH_SEEDS100, fname_asize, 3, True, "word"),
                get_bloomfilter(last_name, hash_runs_lname, HASH_SEEDS100, fname_asize, 3, True, "word"),
                get_bloomfilter(date_of_birth, hash_runs_dob, HASH_SEEDS100, dob_asize, 3, True, "date"),
                get_bloomfilter(gender, hash_runs_gen, HASH_SEEDS100, gender_asize, 3, True, "word")
            ]

    initial_bf      =   bitarray()
    ones = []
    for bf in bf_list: 
        initial_bf.extend(bf)
        ones.append(bf.count(1))


    sim           = []
    sim_dict      = {}

    

    with open(read_filename, 'r', newline='', encoding='utf-8') as read_file:
        reader = csv.reader(read_file)
        next(reader)  
        for row in reader:
            fname, lname, dob, gender, fehler = row
            fname      = fname[:16]
            temp_bf_list =[
                get_bloomfilter(fname, hash_runs_fname, HASH_SEEDS100, fname_asize, 3, True, "word"),
                get_bloomfilter(lname, hash_runs_lname, HASH_SEEDS100, fname_asize, 3, True, "word"),
                get_bloomfilter(dob, hash_runs_dob, HASH_SEEDS100, dob_asize, 3, True, "date"),
                get_bloomfilter(gender, hash_runs_gen, HASH_SEEDS100, gender_asize, 3, True, "word")
            ]   
            temp_bf = bitarray()
            for bf in temp_bf_list: temp_bf.extend(bf)

        
            out, _ = bf_extended_similarity(initial_bf,
                                              temp_bf,
                                              array_sizes, 
                                              ["first_name", "last_name", "birthdate", "gender"],
                                              "total",
                                              [0.98, 0.95, 0.9])
            temp_sim = out[0]
            sim.append((temp_sim, fehler))

            for (val, f) in sim:
                if not f in sim_dict: sim_dict[f] = []
                sim_dict[f].append(val)

    
    with open(write_filename, 'w', newline='', encoding='utf-8') as write_file:
        write_file.write(f"#### Testparameter ####\n\n"
                        f"Testperson:{first_name} {last_name}\n"
                        f"Anzahl Zeichen: {len(first_name+last_name)}\n"
                        f"Anzahl Samples: {samplecount}\n\n"
                        f"Array Größe Vorname: {fname_asize}\n"
                        f"Array Größe Nachname: {lname_asize}\n"
                        f"Array Größe Geschlecht: {gender_asize}\n"
                        f"Array Größe Geburtsdatum: {dob_asize}\n\n"
                        f"Hash-Durchläufe Vorname: {hash_runs_fname}\n"
                        f"Hash-Durchläufe Nachname: {hash_runs_lname}\n"
                        f"Hash-Durchläufe Geburtsdatum: {hash_runs_dob}\n"
                        f"Hash-Durchläufe Geschlecht: {hash_runs_fname}\n\n"                        
                        f"q-Gram size: {2}\n"
                        f"{ones}\n"
                        f"#######################")
        write_file.write("\n\n\n")
        


        for f in FEHLERANZAHL:
            write_file.write(f"Durchschnitt bei {f} Fehlern: {mean(sim_dict[f"{f}"])}\n")
            write_file.write(f"Median bei {f} Fehlern: {median(sim_dict[f"{f}"])}\n")



for x in [35, 40, 45]:
    for y in [20, 25, 30]:

        name_size = achter(250)
        run_typo_test("Lukas", "Meier", "1990-05-12", "Männlich",x, x, y, y,
                        name_size,
                        name_size,
                        achter(150),
                        achter(150), f"{x,y,2}")

# run_typo_test("Lukas", "Meier", "1990-05-12", "Männlich",20, 15, 10, 10, achter(500),achter(200), achter(100), achter(100), f"{20,15,10,10}")