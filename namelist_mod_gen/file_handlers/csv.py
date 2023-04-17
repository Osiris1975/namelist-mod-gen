import csv
import logging
import os
from pathlib import Path

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
