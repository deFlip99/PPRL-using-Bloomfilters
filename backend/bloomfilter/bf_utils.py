from bitarray import bitarray
import mmh3, random, math
from backend.data import normalize_date, normalize_string, gen_qgram
from config import GLOBAL_VAL, BLOOMFILTER_SETTINGS


def get_bloomfilter(text:str , hash_runs:int,
                    hash_seeds:list[int],
                    array_size:int,                   
                    normMode:str,
                    padding:bool = BLOOMFILTER_SETTINGS.PADDING,
                    qSize: int = BLOOMFILTER_SETTINGS.QSIZE) -> bitarray:
    '''
    Function generating the bloomfilter.

    Parameters:
        text (str):                         Any string, which will be fed into the bloomfilter
        hash_sees (list[int]):              List of Seeds, which will be used in the implemented hash-function
        array_size (int):                   Amount of bits in the bloomfilter
        normMode (str = "date" | "word"):   Determines if we use the normalization for words or dates
        padding (bool):                     true = Tom -> _Tom_ , false Tom -> Tom
        qSize (int):                        Size of the generated q-grams; qSize = 2 -> Tom = ["To", "om"]

    Returns:
        bitarray:                           Bloomfilter 
    '''
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


def bf_convert_bytes_to_01(bf_in_bytes) -> str:
    '''
    Function converting the bytes representation of a bloomfilter into zeros and ones.
    
    Parameters:
        bf_in_bytes (BytesLike):    Byte representation of a bloomfilter

    Returns:
        str:                        Zero One representation of a bloomfilter
    '''
    temp = bitarray()
    temp.frombytes(bf_in_bytes)
    return temp.to01()



def bf_add_salt(bf:bitarray, salt_amount: int = 0, salt_fix: list[int] = None):
    '''
    Function used to add 'Salts' (fix or random) to an already existing bloomfilter/bitarray.

    Parameters:
        bf (bitarray):                      The Bloomfilter in which you want to add Salts
        salt_amount (int) (optional):       Adds a given amount of Salts random to the Bloomfilter; default = 0
        salt_fixed (list[int]) (optional):  List of Indices where Salts will be added; will be prefered over salt_amount

    Returns:
        bitarray:                           Bloomfilter with Salts
    '''
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



def bf_sorenson_dice(bitarrayA: bitarray, bitarrayB: bitarray) -> float:
    '''
    Similarity function, calculating the similarity of two bitarrays of the same size, based on the Sorenson-Dice principle

    Parameters:
        bitarrayA (bitarray):       first bitarray
        bitarrayB (bitarray):       second bitarray
    Returns:
        float:                      Similarity of bitarrayA & bitarrayB
    '''
    if len(bitarrayA) != len(bitarrayB): raise ValueError(f"Bitarrays sind nicht gleich lang\n Array A: {len(bitarrayA)}, Array B: {len(bitarrayB)}")
    if not isinstance(bitarrayA, bitarray) or not isinstance(bitarrayB, bitarray):
        raise TypeError("bf_sorenson_dice: both bitarrays need to be the same size")

    intersection = (bitarrayA & bitarrayB).count(1)

    sum_A = bitarrayA.count(1)
    sum_B = bitarrayB.count(1)

    if sum_A + sum_B == 0: return 1.0

    return 2 * intersection / (sum_A + sum_B)


def bf_get_rating(thresholds: list[float], similarity: float) -> str:
    '''
    Helper function which is used to give the similarity a rating

    Parameters:
        threshold (list[float]):    List of thresholds which the rating will be based on
        similarity (float):         Similarity which will be rated
    
    Returns:
        str:                        rating -> ["strong", "medium", "weak", "not alike"]
    '''
    if len(thresholds) != 3: raise SyntaxError("bf_get_rating: threshold needs to be a list of 3 floats")
    if not all(0 < value <= 1.0 for value in thresholds): raise ValueError("bf_get_rating: threshold must contain values between 0 and 1")

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
                           thresholds: list[float] = GLOBAL_VAL.RECORD_LINKAGE_TH,
                           swap: bool = False):
    '''
    Extended function used for a more detailed comparison of two bloomfilters

    Parameters:
        bf1 (bitarray):             Bloomfilter which will be compared to
        bf2 (bitarray):             Bloomfilter we want to compare to others
        array_sizes (list[int]):    List of the segment sizes on the bloomfilter;
                                    e.g.: 100 (first_name), 50 (last_name) ->   first 100 bits corespond to the first_name
                                                                                next 50 bits corespond to the last_name
        array_names (list[str]):    Actual list of names coresponding to different segments on the Bloomfilter;
                                    see first_name, last_name in array_sizes
        out_mode (str):             out_mode = "total", returns the extended similarity for the whole Bloomfilter
                                    out_mode != "total", returns the extended similarity for each segment on the Bloomfilter
        thresholds (list[float]):   List of thresholds used for the similarity rating
        swap (bool) (optional):     If True this function will automatically swap the first and last name if it suspects a swap

    Returns:
        list[float, str, str], bool | list[tuple[float, str, str]], bool
        
    '''
    swaped = False


    assert len(thresholds) == 3, "bf_extended_similarity: thresholds needs to be a list of 3 floats"
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
        if ratings[0] in ["weak", "not alike"] and ratings[1] in ["weak", "not alike"]:
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
