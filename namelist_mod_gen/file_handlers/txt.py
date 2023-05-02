import regex

import namelist_mod_gen.constants.constants as c
from namelist_mod_gen.file_handlers.csv import _get_template_variables
from collections import OrderedDict

def update_name(txt, sub_commas=False):
    for k, v in c.SUB_TOKENS.items():
        if k in txt:
            txt = txt.replace(k, v)
            break
    txt = txt.strip()
    if sub_commas:
        pattern = r'\s+(?=(?:[^"]*"[^"]*")*[^"]*$)'  # matches spaces not inside quotes
        replacement = ','
        txt = regex.sub(pattern, replacement, txt)
    return txt.split(',')


def namelist_txt_to_dict(namelist_file, author, title, namelist_id):
    with open(namelist_file, 'r') as f:
        contents = f.read()

    namelist_dict = OrderedDict()
    namelist_dict['namelist_title'] = [title]
    namelist_dict['namelist_author'] = [author]
    namelist_dict['namelist_id'] = [namelist_id]
    namelist_fields = _get_template_variables()
    for field in namelist_fields:
        if 'namelist' in field:
            continue
        pattern_suffix = r"\s*=\s*{\s*([^}]+)\s*}"
        uncategorized_field = "_".join(field.split("_")[1:])
        if uncategorized_field == "battle_cruiser":
            uncategorized_field = "Battlecruiser"
        if uncategorized_field == "strike_cruiser":
            uncategorized_field = "Strikecruiser"
        if uncategorized_field == "exploration_ship":
            uncategorized_field = "explorationship"
        if "pn_" in field:
            uncategorized_field = f"pc_{field.split('_')[1]}"
            pattern_suffix = r"\s*=\s*{[^}]+names\s*=\s*{\s*([^}]+)\s*}\s*}"
        pattern_string = f"\s+{uncategorized_field}{pattern_suffix}"
        pattern = regex.compile(pattern_string, regex.IGNORECASE)
        match = pattern.search(contents)
        if 'an_' in field:
            if match:
                match_string = match.group(0).replace("\t", " ").replace("\n", " ")
                names = regex.search(r'=\s*\{\s*(?:\w+\s*=)?\s*(".*?")\s*\}', match_string)
                namelist_dict[field] = update_name(names.group(1))
            else:
                namelist_dict[field] = []

        if 'sn_' in field:
            if match:
                match_string = match.group(0).replace("\t", " ").replace("\n", " ")
                names = regex.search(r'{(.*)}', match_string)
                namelist_dict[field] = update_name(names.group(1), True)
            else:
                namelist_dict[field] = []

        if 'cn_' in field:
            if match:
                match_string = match.group(0).replace("\t", " ").replace("\n", " ")
                names = regex.search(r'{(.*)}', match_string, flags=regex.DOTALL)

                namelist_dict[field] = update_name(names.group(1), True)
            else:
                namelist_dict[field] = []
        if 'pn_' in field:
            if match:
                match_string = match.group(0).replace("\t", " ").replace("\n", " ")
                names = regex.search(r'names\s*=\s*{(.+?)\s*(?=})', match_string, flags=regex.DOTALL)

                namelist_dict[field] = update_name(names.group(1), True)
            else:
                namelist_dict[field] = []
        if 'fn_' in field:
            if match:
                match_string = match.group(0).replace("\t", " ").replace("\n", " ")
                names = regex.search(r'sequential_name\s*=\s*"(.+?)"\s*}', match_string, flags=regex.DOTALL)

                namelist_dict[field] = update_name(names.group(1))
            else:
                namelist_dict[field] = []
    return namelist_dict
