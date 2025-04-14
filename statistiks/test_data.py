from bitarray import bitarray

initial_fname   =   "Maximilian"
initial_lname   =   "Schneider"

test_fname = [
    initial_fname,
    "Maxmilian",  
    "Maksimilian",  
    "Maxymilian",  
    "Maxmilien",  
    "Maxmillian"  
]

test_lname = [
    initial_lname,
    "Shneider",  
    "Schnider",  
    "Schnaider",  
    "Schneidr",  
    "Schnejder"  
]
test_daten = [(x, y) for x in test_fname for y in test_lname] + [(x, y) for x in test_fname for y in test_lname]



def prep_test_data(test_set):

    if type(test_set) != list: test_set = [test_set]

    data_prep = []

    for (fname, lname) in test_set:
        data_prep.append([fname, lname, "23101989","meanlich"])
    return data_prep

