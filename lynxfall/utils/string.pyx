#cython: language_level=3
import string
import secrets
from bs4 import BeautifulSoup

def get_token(length: int) -> str:
    secure_str = ""
    for i in range(0, length):
        secure_str += secrets.choice(string.ascii_letters + string.digits)
    return secure_str

def human_format(num: int) -> str:
    if abs(num) < 1000:
        return str(abs(num))
    formatter = '{:.3g}'
    num = float(formatter.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        if magnitude == 31:
            num /= 10
        num /= 1000.0
    return '{} {}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T', "Quad.", "Quint.", "Sext.", "Sept.", "Oct.", "Non.", "Dec.", "Tre.", "Quat.", "quindec.", "Sexdec.", "Octodec.", "Novemdec.", "Vigint.", "Duovig.", "Trevig.", "Quattuorvig.", "Quinvig.", "Sexvig.", "Septenvig.", "Octovig.", "Nonvig.", "Trigin.", "Untrig.", "Duotrig.", "Googol."][magnitude])

def secure_strcmp(val1, val2):
    """
    From Django:
    
    Return True if the two strings are equal, False otherwise. This is a secure function
    """
    return secrets.compare_digest(val1, val2)

def ireplace(old, new, text):
    """Case insensitive replace"""
    idx = 0
    while idx < len(text):
        index_l = text.lower().find(old.lower(), idx)
        if index_l == -1:
            return text
        text = text[:index_l] + new + text[index_l + len(old):]
        idx = index_l + len(new) 
    return text

def replace_last(string, delimiter, replacement):
    start, _, end = string.rpartition(delimiter)
    return start + replacement + end

def ireplacem(replace_tuple, text):
    """Calls ireplace multiple times for a replace tuple of format ((old, new), (old, new)). Can also support regular replace if third flag is set"""
    for replace in replace_tuple:
        if text.startswith("C>"):
            text = text.replace(replace[0], replace[1]).replace("C>", "")
        else:
            text = ireplace(replace[0], replace[1], text)
    return text

def intl_text(text: str, lang: str, dbg: bool = False):
    soup = BeautifulSoup(text, features="lxml")
    for lang_tag in soup.find_all():
        print(lang_tag)
        if lang_tag.name == "fl-lang" and lang_tag.get("code", "") not in (lang, "default", ""):
            lang_tag.decompose()
        
    return str(soup)

