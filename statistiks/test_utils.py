from bitarray import bitarray
import mmh3, random
from test_settings import set_ArraySize, set_HashRuns
from config import DATA_SETTINGS
from backend.data import normalize_date, normalize_string, gen_qgram


def test_bloomfilter(text, hash_runs:int, hash_seeds:list[int], array_size:int, qSize: int , padding:bool, normMode:str) -> bitarray:   
    if normMode == "date": text = [normalize_date(text)]
    elif normMode == "word":
        text = text.split()
        for val in text: val = normalize_string(val)

    bloom_filter = bitarray(array_size)
    bloom_filter.setall(0)

    index = []    
    for val in text:
        qgram_list = gen_qgram(val, qSize, padding)
        for run in range(hash_runs - 1):
            for qgram in qgram_list:
                index += [mmh3.hash(qgram, seed=hash_seeds[run]) % array_size]

    for ix in index:
        if bloom_filter[ix] != 1:
            bloom_filter[ix] = 1

    return bloom_filter

def test_salt(bf:bitarray, salt_amount: int = 0, salt_fix: list[int] = None):

    bf_c = bf.copy()

    if salt_fix:
        for idx in salt_fix:
            if 0 <= idx and idx < len(bf_c):
                bf_c[idx] = 1
    elif salt_amount > 0:
        random_index = random.sample(range(len(bf_c)), min(salt_amount, len(bf_c)))
        for idx in random_index:
            bf_c[idx] = 1
    return bf_c