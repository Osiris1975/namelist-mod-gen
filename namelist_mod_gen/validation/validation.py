import regex


def pi_validate(txt, namelist):
    """
    Validate input text for use in Paradox Interactive games.
    :param txt: text to validate
    :return: list of errors in the string
    """
    errors = []
    has_invalid_character = regex.search(r"[„“‚‘”’…—]", txt)
    if has_invalid_character:
        errors.append(
            f"{namelist}: \"{txt}\" has invalid namelist characters. These characters are not allowed: „ “ ‚ ‘ ” ’ … —")
    if len(txt) > 50:
        errors.append(f"{namelist}: \"{txt}\" is too long. Namelist characters should not exceed 50 characters")
    return errors
