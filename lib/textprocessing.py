import re

sentenceSeparators:list[str] = ['\n', '.', '?', '!'] #note that these MUST be SINGLE CHARACTERS

mediaExtensions:list[str] = [
    #images
    "apng", "gif", "jpg", "jpeg", "jfif", "pjpeg", "pjp", "png", "svg", "webp", "avif", "bmp", "ico", "cur", "tif", "tiff", "heif", "heic",
    #audio
    "3gp", "aac", "act", "aiff", "alac", "amr", "ape", "au", "awb", "dvf", "flac", "gsm", "m4a", "m4b", "mmf", "mp1", "mp2", "mp3", "mpc", "ogg", "oga", "mogg", "opus", "wav", "wma",
    #video
    "webm", "mkv", "flv", "ogv", "gifv", "avi", "mts", "m2ts", "mov", "wmv", "mpg", "mp2", "mpeg", "mpe", "mpv", "m2v", "mp4", "m4p", "m4v"
]

allowedChars_EN:list[str] = [
    ' ', '.', ',', ';', ':', "'", '"', '(', ')', '!', '?', '%', '&', '$', '€',#punctuation
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', #lowercase alphabet
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', #uppercase alphabet
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9' #digits
]
htmlCodes:dict[str,str] = {
    #special characters
    "&deg;" : "°", "&#176;" : "°",
    "&laquo;" : "«", "&#171;" : "«",
    "&raquo;" : "»", "&#187;" : "»",
    "&ndash;" : "–", "&#8211;" : "–",
    "&mdash;" : "—", "&#8212;" : "—",
    "&iexcl;" : "¡", "&#161;" : "¡",
    "&iquest;" : "¿", "&#191;" : "¿",
    "&quot;" : '"', "&#34;" : '"',
    "&ldquo;" : "“", "&#8220;" : "“",
    "&rdquo;" : "”", "&#8221;" : "”",
    "&lsquo;" : "‘", "&#8216;" : "‘",
    "&rsquo;" : "’", "&#8217;" : "’",
    "&nbsp;" : " ", "&#160;" : " ",
    #symbols
    "&amp;" : "&", "&#38;" : "&",
    "&cent;" : "¢", "&#162;" : "¢",
    "&copy;" : "©", "&#169;" : "©",
    "&divide;" : "÷", "&#247;" : "÷",
    "&gt;" : ">", "&#62;" : ">",
    "&lt;" : "<", "&#60;" : "<",
    "&micro;" : "µ", "&#181;" : "µ",
    "&middot;" : "·", "&#183;" : "·",
    "&para;" : "¶", "&#182;" : "¶",
    "&plusmn;" : "±", "&#177;" : "±",
    "&euro;" : "€", "&#8364;" : "€",
    "&pound;" : "£", "&#163;" : "£",
    "&reg;" : "®", "&#174;" : "®",
    "&sect;" : "§", "&#167;" : "§",
    "&trade;" : "™", "&#153;" : "™",
    "&yen;" : "¥", "&#165;" : "¥",
    #diacriticals
    "&aacute;" : "á", "&#225;" : "á",
    "&Aacute;" : "Á", "&#193;" : "Á",
    "&agrave;" : "à", "&#224;" : "à",
    "&Agrave;" : "À", "&#192;" : "À",
    "&acirc;" : "â", "&#226;" : "â",
    "&Acirc;" : "Â", "&#194;" : "Â",
    "&aring;" : "å", "&#229;" : "å",
    "&Aring;" : "Å", "&#197;" : "Å",
    "&atilde;" : "ã", "&#227;" : "ã",
    "&Atilde;" : "Ã", "&#195;" : "Ã",
    "&auml;" : "ä", "&#228;" : "ä",
    "&Auml;" : "Ä", "&#196;" : "Ä",
    "&aelig;" : "æ", "&#230;" : "æ",
    "&AElig;" : "Æ", "&#198;" : "Æ",
    "&ccedil;" : "ç", "&#231;" : "ç",
    "&Ccedil;" : "Ç", "&#199;" : "Ç",
    "&eacute;" : "é", "&#233;" : "é",
    "&Eacute;" : "É", "&#201;" : "É",
    "&egrave;" : "è", "&#232;" : "è",
    "&Egrave;" : "È", "&#200;" : "È",
    "&ecirc;" : "ê", "&#234;" : "ê",
    "&Ecirc;" : "Ê", "&#202;" : "Ê",
    "&euml;" : "ë", "&#235;" : "ë",
    "&Euml;" : "Ë", "&#203;" : "Ë",
    "&iacute;" : "í", "&#237;" : "í",
    "&Iacute;" : "Í", "&#205;" : "Í",
    "&igrave;" : "ì", "&#236;" : "ì",
    "&Igrave;" : "Ì", "&#204;" : "Ì",
    "&icirc;" : "î", "&#238;" : "î",
    "&Icirc;" : "Î", "&#206;" : "Î",
    "&iuml;" : "ï", "&#239;" : "ï",
    "&Iuml;" : "Ï", "&#207;" : "Ï",
    "&ntilde;" : "ñ", "&#241;" : "ñ",
    "&Ntilde;" : "Ñ", "&#209;" : "Ñ",
    "&oacute;" : "ó", "&#243;" : "ó",
    "&Oacute;" : "Ó", "&#211;" : "Ó",
    "&ograve;" : "ò", "&#242;" : "ò",
    "&Ograve;" : "Ò", "&#210;" : "Ò",
    "&ocirc;" : "ô", "&#244;" : "ô",
    "&Ocirc;" : "Ô", "&#212;" : "Ô",
    "&oslash;" : "ø", "&#248;" : "ø",
    "&Oslash;" : "Ø", "&#216;" : "Ø",
    "&otilde;" : "õ", "&#245;" : "õ",
    "&Otilde;" : "Õ", "&#213;" : "Õ",
    "&ouml;" : "ö", "&#246;" : "ö",
    "&Ouml;" : "Ö", "&#214;" : "Ö",
    "&uacute;" : "ú", "&#250;" : "ú",
    "&Uacute;" : "Ú", "&#218;" : "Ú",
    "&ugrave;" : "ù", "&#249;" : "ù",
    "&Ugrave;" : "Ù", "&#217;" : "Ù",
    "&ucirc;" : "û", "&#251;" : "û",
    "&Ucirc;" : "Û", "&#219;" : "Û",
    "&uuml;" : "ü", "&#252;" : "ü",
    "&Uuml;" : "Ü", "&#220;" : "Ü",
    "&szlig;" : "ß", "&#223;" : "ß",
    "&yuml;" : "ÿ", "&#255;" : "ÿ",
    "&#180;" : "´",
    "&#96;" : "`",
}
htmlCodesPattern:re.Pattern = re.compile("|".join(map(re.escape, htmlCodes.keys())))

def findURLs(s:str) -> tuple[list[str], str]:
    """
    Extracts all substrings matching the pattern [x](y) from the input string.

    Parameters:
        s (str): The input string.

    Returns:
        tuple: A list of all y-values found in the pattern, and the string with
               all instances of the pattern removed.
    """
    # Pattern explanation:
    # \[         : literal '['
    # [^\]]*     : any number of characters except ']' (the x part)
    # \]         : literal ']'
    # \(         : literal '('
    # ([^)]*)    : capturing group for any number of characters except ')'
    # \)         : literal ')'
    pattern = r'\[[^\]]*\]\(([^)]*)\)'
    
    # Find all y-values (the content inside parentheses)
    y_list = re.findall(pattern, s)
    
    # Remove every occurrence of the whole pattern
    cleaned_string = re.sub(pattern, '', s)
    
    return (y_list, cleaned_string)

def isolateMediaURLs(urls:list[str], extensions:list[str] = mediaExtensions) -> list[str]:
    """
    From a list of URLs, determines which ones are images (with a very basic check using extensions),
    then puts them in a list. Returns the list of image URLs.
    """
    imgs:list[str] = []
    for url in urls:
        url = url.split("?")[0] #remove modifiers
        if url.split('.')[-1] in extensions:
            imgs.append(url)
    return imgs

def isAbsoluteURL(url:str) -> bool:
    """
    Check if an URL is absolute (returns True) or relative (returns False) with a very basic check (looking if there's a protocol code). 
    """
    if "://" in url[:10]:
        return True
    else:
        return False

def cleanText(original:str, forceAllowed:bool = False, allowed:list[str]=allowedChars_EN, htmlCodes:dict[str,str]=htmlCodes, pattern:re.Pattern = htmlCodesPattern) -> str:
    """
    Cleans an original string from weird HTML codes and (if forceAllowed-(bool) = True), also removes every character which is not in the list allowed-(list[str]),
    then returns the cleaned string.
    Consider that allowed is set by default to the list allowedChars_EN, which only includes characters from the English language. You must provide your own list for other languages.
    """
    filtered:str = pattern.sub(lambda match: htmlCodes[match.group(0)], original)
    if forceAllowed:
        filtered = ''.join([char for char in filtered if char in allowed])
    return filtered

def joinWithSeparator(s1:str, s2:str, sep:str):
    """
    Join two strings ensuring exactly one separator appears between them.
    Removes any extra separators from the end of s1 and the start of s2.
    """
    return s1.rstrip(sep) + sep + s2.lstrip(sep)

def oneLiner(original: str, punctuation:list[str] = ['.', ',', ';', '!', '?', '-', '"', "'", "("]) -> str:
    """
    Replace newlines in the input string according to the punctuation before them.
    
    For each newline character:
    - If the character immediately before it is punctuation, replace the newline with a space.
    - Otherwise, replace the newline with a dot followed by a space (". ").
    
    Punctuation is defined as all characters in string.punctuation.
    
    Args:
        original: Input string that may contain newlines.
    
    Returns:
        A string with newlines replaced as described.
    """
    result = []
    for i, ch in enumerate(original):
        if ch == '\n':
            # Check if there is a preceding character and if it is punctuation
            if i > 0 and original[i-1] in punctuation:
                result.append(' ')
            else:
                result.append('. ')
        else:
            result.append(ch)
    return ''.join(result)

def find(text: str, pattern: str) -> list[int]:
    """
    Return a list of starting indices where `pattern` occurs in `text`.
    Overlapping occurrences are included.
    """
    if not pattern or len(pattern) > len(text):
        return []

    indices = []
    pattern_len = len(pattern)
    # Loop over every possible start position
    for i in range(len(text) - pattern_len + 1):
        if text[i:i + pattern_len] == pattern:
            indices.append(i)
    return indices

def deleteSentence(text:str, index:int, separators:list[str]=sentenceSeparators) -> str:
    """
    Given the index of a character in a given text, removes the whole sentence where it is contained and returns the modified string.
    A sentence is defined as the maximal substring that does not contain any of the provided separator strings. 
    The separator that ends the sentence (if present) is also removed. 
    If `index` falls inside a separator, that separator is considered part of the sentence it terminates.
    """
    if not 0 <= index < len(text):
        raise ValueError("Index out of range")
    # If no separators are given, the whole text is one sentence
    if not separators:
        return ""

    n = len(text)
    # 1. Find the start of the sentence (character right after the last separator before index)
    start = 0
    for i in range(index - 1, -1, -1):
        if text[i] in separators:
            start = i + 1
            break
    # 2. Find the end of the sentence (the next separator at or after index, or the end of text)
    end = n
    for i in range(index, n):
        if text[i] in separators:
            end = i + 1   # include the separator itself
            break
    # 3. Remove the slice from start to end
    return text[:start] + text[end:]

def deleteMultipleSentences(text: str, indices: list[int], separators: list[str]=sentenceSeparators) -> str:
    """
    Removes multiple sentences from a text, given a list of character indices.
    Each index identifies a sentence to remove (the sentence containing that character).
    The function uses deleteSentence() repeatedly, handling the index shifts that occur
    after each removal.

    Parameters:
    - text: the original string.
    - indices: list of character positions (0‑based) in the original text.
    - separators: list of strings that mark sentence boundaries (same as in deleteSentence).

    Returns:
    - The modified string with all specified sentences removed.
    """
    if not indices:
        return text

    # Helper: find the start and end of the sentence containing a given index.
    def _sentence_bounds(txt: str, idx: int, seps: list[str]) -> tuple[int, int]:
        if not 0 <= idx < len(txt):
            raise ValueError("Index out of range")
        if not seps:
            # No separators -> whole text is one sentence
            return (0, len(txt))

        n = len(txt)
        # Find start (right after the last separator before idx, or 0)
        start = 0
        for i in range(idx - 1, -1, -1):
            if txt[i] in seps:
                start = i + 1
                break
        # Find end (the next separator at or after idx, or end of text)
        end = n
        for i in range(idx, n):
            if txt[i] in seps:
                end = i + 1   # include the separator
                break
        return (start, end)

    # Collect unique sentence intervals from the original text
    intervals = set()
    for idx in indices:
        s, e = _sentence_bounds(text, idx, separators)
        intervals.add((s, e))

    # Sort intervals by start position descending (remove later sentences first)
    sorted_intervals = sorted(intervals, key=lambda x: x[0], reverse=True)

    # Apply deletions in that order
    result = text
    for s, _ in sorted_intervals:
        # s is still a valid index in the current result because all removals so far
        # have been after this position.
        result = deleteSentence(result, s, separators)

    return result
