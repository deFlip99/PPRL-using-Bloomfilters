from backend.bloomfilter import get_bloomfilter, bf_extended_similarity
from bitarray import bitarray

# bf = get_bloomfilter("11/09/2022", 10, [234,134,56245,745,1354,5756,1345,73567,1346,7891,51834], 500, 2, False, "date")

def achter(n:int) -> int:
    if n % 8 == 0: return n
    else: return n + (8 - (n % 8))


test_same = bitarray('10100110011111011001')
print(bf_extended_similarity([5,5,5,5], ['name1', 'name2', 'name3', 'name4'],test_same, test_same))
test_swap1 = bitarray('11101101001111011001')
test_swap2 = bitarray('10100110011111011001')
print(bf_extended_similarity([5,5,5,5], ['name1', 'name2', 'name3', 'name4'],test_swap1, test_swap2))
