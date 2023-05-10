import csv
import logging
import os
from pathlib import Path
from collections import OrderedDict

import jinja2schema
import regex

import constants.constants as c
from clean.cleaner import clean_input_text

log = logging.getLogger('NMG')


def csv_to_dicts(namelist_file, author):
    """
    Converts namelist_file to a dictionaru
    :param author: namelist author as passed in via command line
    :param namelist_file: Path to a CSV namelist file
    :return:
    """

    # Create dictionary of cleaned texts
    namelist_dict = {key: [] for key in _get_template_variables()}
    with open(namelist_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            for k, v in row.items():
                if k in namelist_dict.keys() and len(v) > 0:
                    clean_text = clean_input_text(v)
                    namelist_dict[k].append(clean_text)

    # Generate localization keys
    for k, v in namelist_dict.items():
        if k not in c.UNKEYED_FIELDS and len(v) > 0:
            values = create_keyed_dict(k, v, author, namelist_dict['namelist_id'][0])
            namelist_dict[k] = values
    return namelist_dict


def create_keyed_dict(key, values, author, namelist_id):
    """
    Builds key value pairs using a generated reference key and values associated with it.
    :param key: The namelist-level key, or category, as specified in the CSV file. Analagous to a column in the CSV.
    :param values: The values associated with the namelist category.
    :param author: author of the namelist, for use in building a reference key.
    :param namelist_id: The ID of the namelist to be used in building a reference key.
    :return:
    """
    if len(values) > 1:
        vdict = dict()
        for v in values:
            value_key = f'{author}_{namelist_id}_{key}_{v}'
            value_key = regex.sub('[^0-9a-zA-Z]+', '_', value_key).upper()
            vdict[value_key] = [v]
        return vdict
    else:
        value_key = regex.sub('[^0-9a-zA-Z]+', '_', key).upper()
        return {f"{author.upper()}_{namelist_id.upper()}_{value_key}": values}


def csv_template(dest):
    """
    Dumps a CSV template that can be populated and used as input for the tool.
    :param dest: The location to dump the CSV template to.
    :return:
    """
    fields = _get_template_variables()
    with open(dest, 'w', newline='\n') as file:
        writer = csv.writer(file)
        writer.writerow(fields)


def _get_template_variables():
    variables = jinja2schema.infer(Path(os.path.join(c.TEMPLATES_DIR, "namelist.txt")).read_text())
    meta_list = ['namelist_title', 'namelist_author', 'namelist_id']
    objects = []
    for category in variables.items():
        if category[0] not in meta_list:
            objects.append(category[0])
    objects.sort()
    meta_list.extend(objects)
    return meta_list


def create_template(dest_file):
    """
    Proxy function for csv_template function.
    :param dest_file:
    :return:
    """
    try:
        if not dest_file.endswith('csv'):
            dest_file = f'{dest_file}.csv'
        csv_template(dest_file)
        log.info(f'Template csv file written to {dest_file}')
    except Exception as e:
        log.critical(f'Template creation failed: {e}')


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
