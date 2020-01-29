with open("hiragana.csv", "r", encoding="UTF8") as f:
    hiragana_rows = [row.split(',') for row in f]
    for row in hiragana_rows:
        for i, item in enumerate(row):  # removing trailing white-space chars
            result = item.rstrip()
            row[i] = result


with open("transcriptions.csv", "r") as f:
    transcriptions_rows = [row.split(',') for row in f]
    for row in transcriptions_rows:
        for i, item in enumerate(row):
            result = item.rstrip()
            row[i] = result


d = {}
dakuten = "\N{COMBINING KATAKANA-HIRAGANA VOICED SOUND MARK}"
handakuten = "\N{COMBINING KATAKANA-HIRAGANA SEMI-VOICED SOUND MARK}"

# building a dict of hiragana-transcription pairs and adding missing characters
for hira, trans in zip(hiragana_rows[1:], transcriptions_rows[1:]):
    for i in range(len(hira))[1:]:
        d[hira[i]] = trans[i]
    d[hira[2] + dakuten] = "g" + trans[2][-1:]
    if hira[3] == 'し':
        d[hira[3] + dakuten] = "j" + trans[3][-1:]
    else:
        d[hira[3] + dakuten] = "z" + trans[3][-1:]
    if hira[4] == 'ち':
        d[hira[4] + dakuten] = "j" + trans[4][-1:]
    elif hira[4] == 'つ':
        d[hira[4] + dakuten] = "z" + trans[4][-1:]
    else:
        d[hira[4] + dakuten] = "d" + trans[4][-1:]
    d[hira[6] + dakuten] = "b" + trans[6][-1:]
    d[hira[6] + handakuten] = "p" + trans[6][-1:]

d["\N{HIRAGANA LETTER SMALL YA}"] = "ya"
d["\N{HIRAGANA LETTER SMALL YU}"] = "yu"
d["\N{HIRAGANA LETTER SMALL YO}"] = "yo"
d["\N{HIRAGANA LETTER SMALL TU}"] = ""
d[dakuten] = ''
d[handakuten] = ''
d[' '] = ''

    
def hepburn(*hiragana, long_vowel="macron", **kwargs):  
    """Returns a list of transcribed strings.
    
    
    Args:
        hiragana: a single string, multiple strings or a list of strings, 
                  each containing a Japanese word written in hiragana
        long_vowel: argument indicating how long vowels ought to be transcribed
        kwargs: any other keyword argument
        
    Returns:
        list: a list of transcribed strings, corresponding to 
              the transcription of the input strings it received  
    
    Raises:
        ValueError: if no argument is passed
                    if hiragana argument is not a string, a list or a tuple 
                    if keyword argument 'long_vowel' is declared with 
                    anything else than "h", "macron" or "native"
                    if any other keyword argument is passed
                    if a string contains non-hiragana characters
        
    """
    if not hiragana:
        raise ValueError    
    if type(hiragana) not in [str, list, tuple]:
        raise ValueError
    if long_vowel not in ["macron", "h", "native"]:
        raise ValueError
    if kwargs:
        raise ValueError

    transcribed_words = []
    for element in hiragana:
        if type(element) == list:
            for string in element:
                for char in string:
                    if char not in d:
                        raise ValueError
                transcribed_word = transcriber(string, long_vowel)      
                transcribed_words.append(transcribed_word)
        else:
            for string in element.split():
                for char in string:
                    if char not in d:
                        raise ValueError
                transcribed_word = transcriber(string, long_vowel)
                transcribed_words.append(transcribed_word)
    return transcribed_words


def transcriber(string, long_vowel):
    """Returns a transcribed string.
    
    
    Iterates over character pairs of a string and transcribes them 
    according to the Hepburn Romanization Method. Calls other functions 
    designed for each specific case to do so. Transcribed characters of
    special cases are kept in a list so as not to transcribe them twice.

    Args:
        string: a Japanese word written in hiragana
        long_vowel: argument indicating how long vowels ought to be transcribed
    Returns:
        string: a romanized string
            
    """
    word = ''
    chars = list(string)
    for idx, item in enumerate(chars):  # combining marker with previous char
        if idx < len(chars)-1:
            if chars[idx+1] == dakuten or chars[idx+1] == handakuten:
                chars[idx] = chars[idx] + chars.pop(idx+1)
    next_chars = chars[1:]
    next_chars.append('')

    if len(chars) == 1:
        word = char_transcriber(chars[0])
    else:
        char_pairs = list(zip(chars, next_chars))
        transcribed = []
        for idx, (a, b) in enumerate(char_pairs):
            nextelem = char_pairs[(idx + 1) % len(char_pairs)]
            next_a, next_b = nextelem
            if nasal(a, b):
                word += nasal(a, b)
                transcribed.append(a)
            elif lengthened_sound(a, b, long_vowel):
                word += lengthened_sound(a, b, long_vowel)
                transcribed.append(a)
                transcribed.append(b)
            elif geminate(a, b):
                word += geminate(a, b)
                transcribed.append(b)
            elif palatalized(a, b):
                if lengthened_sound(next_a, next_b, long_vowel):
                    word += palatalized(a, b, following="long vowel")
                else:
                    word += palatalized(a, b)
                transcribed.append(a)
                transcribed.append(b)
            elif a not in transcribed:
                word += char_transcriber(a)
    return word


def char_transcriber(char):
    """Returns corresponding mora transcription of a character."""
    for k, v in d.items():
        if char == k:
            char = v
    return char


def lengthened_sound(a, b, long_vowel):
    """Transcribes a long vowel according to one of the three manners."""
    if b in ['あ', 'い', 'う', 'え', 'お']:
        a = char_transcriber(a)
        b = char_transcriber(b)
        # checking if a and b correspond to the same vowel or to 'う' exception
        if a[-1:] == b[-1:] or a[-1:] == 'o' and b[-1:] == 'u':
            if long_vowel == "macron":
                a = a + "\N{COMBINING MACRON}"
            elif long_vowel == "h":
                a = a + "h"
            elif long_vowel == "native":
                a = a + "u"
            return a
    return False


def geminate(a, b):
    """Duplicates the first letter of the transcribed mora."""
    if a == 'っ':
        b = char_transcriber(b)
        return b[0] + b
    return False


def palatalized(a, b, following="..."):
    """Transcribes a palatalized vowel, skips b if followed by long vowel."""
    if b in ['ゃ', 'ゅ', 'ょ']:
        a2 = char_transcriber(a)
        b2 = char_transcriber(b)
        if a in ['し', 'ち']:
            if following == "long vowel":  
                return a2[:2] 
            else:
                return a2[:2] + b2[1:]
        elif a in ['じ', 'ぢ']:
            if following == "long vowel":
                return a2[0]
            else:
                return a2[0] + b2[1:]
        else:
            if following == "long vowel":
                return a2[0]
            else:
                return a2[0] + b2
    return False


def nasal(a, b):
    """Returns "n'" when 'ん' precedes a vowel or a mora from the N column."""
    a2 = char_transcriber(a)
    b2 = char_transcriber(b)
    if a == 'ん':
        if not b:  # if 'ん' is the last character
            return a2
        elif len(b2) == 1 or b2[0] == 'n':
            return a2 + "'"
        else:
            return a2
    return False
