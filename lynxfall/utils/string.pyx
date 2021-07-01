#cython: language_level=3
import string
import secrets

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

def intl_text(text: str, lang: str, link: bool = False, linked_langs: dict = {}, dbg = False):
    """Text internationalizer"""
    logger.trace(f"Called intl_text with text of {text}, lang of {lang}, link of {link} and linked_langs of {linked_langs}")
    lang = lang if lang.replace(" ", "") else "default" # If lang is empty/none, set it to default, otherwise keep the lang
    ltext = text.split(f"[[lang {lang.lower()}") # Split text into sections
    if len(ltext) == 1: # We didnt get any sections
        # Only one language or specified language is not found
        if link:
            return "" # Return nothing if link was not found
        kwargs = {"link": link, "linked_langs": linked_langs | {lang: None}} # Common keyword arguments for returning
        if lang == "default" and "[[lang en" in text: # If lang is default, there are no translations for it and en translations have been seen/potentially there, use them
            return intl_text(text, "en", **kwargs) 
        if lang != "default": # Fallback to default translations if this language has not been found
            return intl_text(text, "default", **kwargs)
        return text # Otherwise, if all fails, return the full text
    strlst = [] # List of all sections with this language is in strlst
    i = 0 # Counter

    # Some math:
    # For a<b>c<b>d<b>e<b>ffg
    # Split by <b> is a, c, d, e, ffg
    # a, d, ffg are between or not in <b>. These are index 0, 2 and 4
    # So, odd is in between and even is not
    # So to get in between, do i % 2 as below

    for text_block in ltext:
        if i % 2 == 0:
            i+=1
            continue # Meaning before or between a lang tag, see "Some math..."
        i+=1
        txt_split = text_block.split("]]", 1) # The split in the beginning got us "link=foo label=baz]] My text here", inthis the metadata if link=foo label=baz is before the ]] and the text is after, so split by ]] once to get metadata and inside text
        if len(txt_split) == 1: # This happens when a user forgets to close their tag, ignore the full tag and contents
            i+=1
            continue # Illegal lang attribute
        
        txt_add = txt_split[1] # Text add is after ]]
        
        # Get meta as string of a=1 b=2 and make it {"a": 1, "b": 2}
        meta_str = txt_split[0] # Metadata string is before ]]

        meta = {} # Metadata dict to dump proccessed metadata into
        
        # List of metadata attributes about our section to forward handle (abc=def abcx fgh=a will give {"abc" def abcx, "fgh": a} where abcx is forward handled)
        forward_handling = None # Whether we are currently processing something that needs to be handled
        for split in meta_str.split(" "): # Split it into [a=b, c=d] where original was a=b c=d
            
            split_list = split.replace(" ", "").split("=") # Then make the a=b into [a, b]
            
            if len(split_list) != 1: # We have a equal to sign!!!
                
                if split_list[1].startswith('"') or split_list[1].startswith("'"):
                    forward_handling = split_list[0] # Start forward handle at begin quotes
                    
                elif split_list[1].endswith('"') or split_list[1].endswith("'"):
                    forward_handling = None # Stop forward handle at quotes
                    
                meta |= {split_list[0]: split_list[1]} # Add to meta
                
            elif forward_handling: # Handle forward handling
                meta[forward_handling] += " " + split_list[0] # Add on split stuff
                
        pre = None # Default no pre (inheritance)
        
        link_opt = meta.get("link")
        if link_opt:
            lang_link = link_opt
            if lang_link.replace(" ", "") == lang.replace(" ", "") or lang_link in linked_langs.keys():
                pre = linked_langs.get(lang_link)
            else:
                pre = intl_text(text, lang_link, link = True, linked_langs = linked_langs | {lang_link: txt_add})
        if pre:
            if not txt_add.replace(" ", ""):
                txt_add = pre # Handle cases of default aliasing to en and viceversa
            else:
                txt_add = pre + "\n" + txt_add
        strlst.append(txt_add)
        if dbg:
            return "\n".join(strlst), strlst, meta
    return "\n".join(strlst)
