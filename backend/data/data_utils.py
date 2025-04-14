from config import DATA_SETTINGS
from dateutil import parser
import re


#create qGrams of size q
def gen_qgram(text: str, q: int, padding: bool) -> list[str]:
        
        if padding: text = "_" + text + "_"
        result = []
        
        for i in range(len(text) - (q -1)):               
                result.append(text[i:i + q])
        return result


def normalize_string(text:str, toUpper: bool = True) -> str:
        titles = r"|".join(map(re.escape, DATA_SETTINGS.REMOVE_TITLES))
        text = re.sub(titles + r"\s*", "",text).strip().replace("-", " ")
        text

        for letter, replacement in DATA_SETTINGS.REPLACE_LETTERS.items():
                text = re.sub(letter, replacement, text.lower())

        if toUpper: return text.upper()
        else: return text.capitalize()


def normalize_date(date:str) -> str:
        try:
                date_obj = parser.parse(date)
                return date_obj.strftime("%Y%m%d")
        except Exception as e:
                return date