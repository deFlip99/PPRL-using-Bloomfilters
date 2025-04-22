#BLOOMFILTER Settings
# import math

# def set_ArraySize(n:int, p: int):
#     result = math.ceil((- n * math.log(p)) / (math.log(2) ** 2))
#     return (result + (8 - (result % 8)))

# def set_HashRuns(n:int, m:int):
#     return math.ceil((m / n) * math.log(2))

class BLOOMFILTER_SETTINGS:
    # ITEM_AMOUNT                 = 100
    # FALSE_POSITIVE_LIKELIHOOD   = 0.001
    # ARRAY_SIZE                  = 2000

    ARRAY_SIZES                 = {  'name'         :  800,
                                    'other'       :   208}


    HASHRUNS_NAME               =   40  
    HASHRUNS_OTHER              =   20


    HASH_SEEDS40                = [92607, 52434, 47751, 48121, 85922, 41346, 94666, 69197, 70631, 55028, 54016, 34796, 13109, 16195, 19751, 96272, 73586, 40463, 63191, 46483, 13355, 99604, 95695, 57705, 37429, 36962, 13566, 11983, 91392, 97360, 12860, 12034, 78921, 61329, 47746, 84304, 62186, 26965, 15924, 59290]
    HASH_SEEDS20                = [88036, 17196, 37991, 66185, 82094, 19288, 94058, 70969, 93056, 19427, 67473, 81898, 40778, 20010, 64626, 90518, 20943, 17182, 39574, 37951]


    SALT_AMOUNT                 = 0
    SALT_FIX                    = None
    

    QSIZE                       = 2
    PADDING                     =   True


