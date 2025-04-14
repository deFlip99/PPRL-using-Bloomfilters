from bitarray import bitarray
import mmh3, random, math
from backend.data import normalize_date, normalize_string, gen_qgram

#create BloomFilter
def get_bloomfilter(text, hash_runs:int, hash_seeds:list[int], array_size:int, qSize: int , padding:bool, normMode:str, toUpper:bool=True) -> bitarray:
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


def bf_convert_blob_to_bf(blob) -> bitarray:
    temp = bitarray()
    temp.frombytes(blob)
    return temp.to01()


#Füge beliebigem bitarray einen random oder fixen Salt hinzu
def bf_add_salt(bf:bitarray, salt_amount: int = 0, salt_fix: list[int] = None):

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


#Similarity with Sorenson-Dice
def bf_sorenson_dice(bitarrayA: bitarray, bitarrayB: bitarray) -> float:
    if len(bitarrayA) != len(bitarrayB): raise ValueError(f"Bitarrays sind nicht gleich lang\n Array A: {len(bitarrayA)}, Array B: {len(bitarrayB)}")

    intersection = (bitarrayA & bitarrayB).count(1)

    sum_A = bitarrayA.count(1)
    sum_B = bitarrayB.count(1)

    if sum_A + sum_B == 0: return 1.0

    return 2 * intersection / (sum_A + sum_B)


def bf_get_rating(thresholds: list[float], similarity: float) -> str:
    if similarity > thresholds[0]:
        return "strong"
    elif thresholds[0] > similarity >= thresholds[1]:
        return "medium"
    elif thresholds[1] > similarity >= thresholds[2]:
        return "weak"
    else:
        return "not alike"


def bf_extended_similarity(bf1: bitarray,
                           bf2: bitarray,
                           array_sizes: list[int],
                           array_names: list[str],
                           out_mode: str = None,
                           thresholds: list[float] = None,
                           swap: bool = False):
    """
    out_mode: 
    Für "total" werden alle Ähnlichkeiten Zusammengerechnet. return = [similarity, "total", rating], SwapedBool
    Für None werden die Ähnlichkeiten seperat ausgegeben. return = [(similarity, "vorname", rating),...], SwapedBool
    """
    swaped = False

    # Default-Parameter initialisieren
    if thresholds is None:
        thresholds = [0.95, 0.87, 0.6]
    else:
        assert len(thresholds) == 3, "Die Liste an thresholds muss genau 3 Werte enthalten"
    thresholds = sorted(thresholds, reverse=True)

    bf1_dict = {}
    bf2_dict = {}
    section_similarity = []

    start = 0
    # Erzeuge Dictionarys und berechne Ähnlichkeiten für jeden Abschnitt.
    for size, name in zip(array_sizes, array_names):
        end = start + size
        bf1_section = bf1[start:end]
        bf2_section = bf2[start:end]
        bf1_dict[name] = bf1_section
        bf2_dict[name] = bf2_section

        similarity = bf_sorenson_dice(bf1_section, bf2_section)
        rating = bf_get_rating(thresholds, similarity)
        section_similarity.append((similarity, name, rating))

        start = end

    ratings = [rating for (_, _, rating) in section_similarity]


    if len(ratings) >= 4:
        # Überprüft, ob der Vorname von bf1 nicht ähnlich zum Nachnamen von bf2 ist.
        if ratings[0] == ratings[1] == "not alike":
            if not (ratings[2] == ratings[3] == "not alike"):
                new1 = bf_sorenson_dice(bf1_dict[array_names[0]], bf2_dict[array_names[1]])
                new2 = bf_sorenson_dice(bf1_dict[array_names[1]], bf2_dict[array_names[0]])
                if section_similarity[0][0] < new1 > thresholds[-1] and section_similarity[1][0] < new2 > thresholds[-1]:
                    swaped = True
                    if swap:
                        section_similarity[0] = (new1, section_similarity[0][1], "swaped")
                        section_similarity[1] = (new2, section_similarity[1][1], "swaped")
                    

    if out_mode == "total":
        similarities = [sim for (sim, _, _) in section_similarity]
        total_similarity = math.fsum(similarities) / len(similarities) if similarities else 0.0
        combined_rating = bf_get_rating(thresholds, total_similarity)
        return [total_similarity, "total",combined_rating], swaped
    else:
        return [section_similarity], swaped
