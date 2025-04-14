class DATA_SETTINGS:
    REMOVE_TITLES               =   ["Dr.", "dr.", "med.", "nat.", "Prof.", "Mr.", "Mrs.","Dipl.-Ing.", "Dipl.-Kfm.", "M.A.", "M.Sc.", "B.A.", "B.Sc.", "Ph.D.", "M.D.", "LL.M.", "MBA", "Ing.", "Arch.",]
    REPLACE_LETTERS             =   {
        r"[àáâãäåāă]": "a",
        r"[èéêëēĕ]": "e",
        r"[ìíîïīĭ]": "i",
        r"[òóôõöøōŏ]": "o",
        r"[ùúûüūŭ]": "u",
        r"[ýÿŷ]": "y",
        r"[çćĉċč]": "c",
        r"[ðďđ]": "d",
        r"[ĝğġģ]": "g",
        r"[ĥħ]": "h",
        r"[ĵ]": "j",
        r"[ķĸ]": "k",
        r"[ĺļľŀł]": "l",
        r"[ńņňŉŋ]": "n",
        r"[ŕŗř]": "r",
        r"[śŝşš]": "s",
        r"[ţťŧ]": "t",
        r"[ŵ]": "w",
        r"[źżž]": "z",
        r"[æ]": "ae",
        r"[œ]": "oe",
        r"[ß]": "ss",
        r"[þ]": "th"
}
    



class TEST_DATA_SETTINGS:
    AMOUNT_OF_TEST_DATA         = 500
    

