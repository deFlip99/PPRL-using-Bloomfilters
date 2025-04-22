from config import DATA_SETTINGS
from dateutil import parser
import re



def gen_qgram(text: str, q: int, padding: bool) -> list[str]:
        """
        Generate a list of q‑grams (substrings of length q) from the given text,
        optionally padding the text with underscores.

        Parameters:
                text (str): Input text to split into q‑grams.
                q (int): Length of each q‑gram (must be >= 1).
                padding (bool): If True, pads the text with one underscore at the start and end.

        Returns:
                list[str]: List of generated q‑grams.
        """

        if q < 1: raise ValueError(f"gen_qgram: 'q' must be at least 1 (given: {q})")

        if padding: text = f"_{text}_"
        
        if q > len(text): return []

        return [text[i:i + q] for i in range(len(text) - q + 1)]


def normalize_string(text: str, to_upper: bool = True) -> str:
        """
        Remove predefined titles and hyphens, replace characters by a mapping, 
        and adjust the casing of the resulting string.

        Parameters:
                text (str):             The input string to normalize.
                to_upper (bool):        If True, convert the final string to uppercase.
                                        If False, capitalize only the first letter.

        Returns:
                str:            Normalized version of the input.
        """
        #Strip out any titles defined in DATA_SETTINGS.REMOVE_TITLES
        titles_pattern = r"|".join(map(re.escape, DATA_SETTINGS.REMOVE_TITLES))
        text = re.sub(fr"{titles_pattern}\s*", "", text)
        
        #Replace hyphens with spaces
        text = text.strip().replace("-", " ")

        text = text.lower()

        #Apply character replacements from DATA_SETTINGS.REPLACE_LETTERS
        for pattern, replacement in DATA_SETTINGS.REPLACE_LETTERS.items():
                text = re.sub(pattern, replacement, text)
        
        return text.upper() if to_upper else text.capitalize()


def normalize_date(date_str:str) -> str:
        """
        Parse an input date string into YYYYMMDD format, returning the original string on parse failure.

        Parameters:
                date_str (str):   The date string to normalize (e.g. "2025-04-17", "April 17, 2025", "17/04/2025").

        Returns:
                str: A string in "YYYYMMDD" format if parsing succeeds; otherwise returns the original input.
        """
        try:
                parsed = parser.parse(date_str)
                return parsed.strftime("%Y%m%d")
        except Exception as e:
                return date_str