import regex


def pi_validate(txt, text):
    """
    Validate input text for use in Paradox Interactive games.
    :param text: text from namelist to validate
    :param txt: text to validate
    :return: list of errors in the string
    """
    errors = []
    has_invalid_character = regex.search(r"[„“‚‘”’…—]", txt)
    if has_invalid_character:
        errors.append(
            f"{text}: \"{txt}\" has invalid namelist characters. These characters are not allowed: „ “ ‚ ‘ ” ’ … —")
    if len(txt) > 30:
        errors.append(f"{text}: \"{txt}\" exceeds some in-game text box limits and may be truncated.")
    return errors
