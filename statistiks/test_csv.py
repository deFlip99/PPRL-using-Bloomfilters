import csv, random, string, os
from test_settings import FEHLERANZAHL

def introduce_errors(data, num_errors):
    data_list = list(data)
    indices = [i for i in range(len(data_list)) if data_list[i] != ',']
    error_positions = random.sample(indices, num_errors)
    
    for i in error_positions:
        if data_list[i].isdigit():
            data_list[i] = random.choice(string.digits)
        else:  
            data_list[i] = random.choice(string.ascii_letters)
    
    return ''.join(data_list)

def generate_csv(fname: str, lname: str, dob:str, gender: str, samplecount: int, filename: str ):
    original = f"{fname},{lname},{dob},{gender}"
    errors_per_group = FEHLERANZAHL
    entries_per_group = samplecount
    filename = f"statistiks/typo_{filename}.csv"
    if not os.path.exists(filename):
        with open(filename, 'w', newline='', encoding='utf-8') as file:      
            writer = csv.writer(file)
            writer.writerow(["Vorname", "Nachname", "Geburtsdatum", "Geschlecht", "Fehler"])
            
            for num_errors in errors_per_group:
                for _ in range(entries_per_group):
                    corrupted = introduce_errors(original, num_errors)
                    writer.writerow(corrupted.split(',') + [f"{num_errors}"])
    
    
