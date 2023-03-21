from collections import Counter
from difflib import get_close_matches

import regex


def validate(txt):
    errors = []
    has_invalid_character = regex.search(r"[„“‚‘–”’…—]", txt)
    if has_invalid_character:
        errors.append(f"{txt} has invalid namelist characters. These characters are not allowed: „ “ ‚ ‘ – ” ’ … —")
    if len(txt) > 50:
        errors.append(f"{txt} is too long. Namelist characters should not exceed 50 characters")
    return errors


def validate_translation(trans_array, original_txt):
    matches = get_close_matches(original_txt, trans_array)
    if len(matches) > 0:
        return matches[0]
    occurence_count = Counter(trans_array)
    counts = sorted(occurence_count.values())
    ct_array = [len(occurence_count.most_common(1)[0][0].split(' ')), len(original_txt.split(' '))]
    ct_array.sort()
    if counts[-1] > 1 and ct_array[1] - ct_array[0] < 2:
        return occurence_count.most_common(1)[0][0]
    if len(trans_array) == 0:
        return original_txt
    else:
        return validate_translation(trans_array[:-1], trans_array[0])
