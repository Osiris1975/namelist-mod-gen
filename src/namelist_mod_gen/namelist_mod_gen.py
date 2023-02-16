#!/usr/bin/env python

import argparse
import constants as c
import csv
from jinja2 import Environment, FileSystemLoader
import jinja2schema
import os
import sys
import re
from pathlib import Path
from collections import OrderedDict

template_loader = FileSystemLoader(searchpath=c.TEMPLATES_DIR)
template_env = Environment(loader=template_loader)


def make_mod_directories(mod_name, lang):
    dirs = {
        "namelist": os.path.join(c.MOD_OUTPUT_DIR, mod_name, 'common', 'name_lists'),
        "localization": os.path.join(c.MOD_OUTPUT_DIR, mod_name, 'localisation', lang)
    }

    for d in dirs.values():
        if not os.path.exists(d):
            os.makedirs(d)
    return dirs


def create_mod(args):
    dirs = make_mod_directories(args.mod_name, 'english')
    nl_dict, ord_dict = csv_to_dicts(args.namelist_csv)

    name_list_file = os.path.join(dirs["namelist"], f"{nl_dict['namelist_id']}.txt")
    with open(name_list_file, 'w') as file:
        namelist_template = template_env.get_template(c.NAMELIST_TEMPLATE)
        name_list = namelist_template.render(nl_dict)
        file.write(name_list)
        print(f'Namelist file written to {name_list_file}')

    namelist_loc_file = os.path.join(dirs["localization"], f"{nl_dict['namelist_author'].lower()}_namelist_l_english.yml")
    with open(namelist_loc_file, 'w') as file:
        nl_loc_template = template_env.get_template(c.LOCALIZATION_TEMPLATE)
        nl_loc_dict = {
            nl_dict['namelist_id']: {
                'id': nl_dict['namelist_id'].lower(),
                'author': nl_dict['namelist_author'].lower(),
                'title': nl_dict['namelist_title']
            }
        }
        nl_loc = nl_loc_template.render(dict_item=[nl_loc_dict])
        file.write(nl_loc)
        print(f'Namelist localization file written to {name_list_file}')

    ord_loc_file = os.path.join(dirs["localization"], f"name_list_{nl_dict['namelist_id'].upper()}_l_english.yml")
    with open(ord_loc_file, 'w') as file:
        ord_loc_template = template_env.get_template(c.ORD_NAMES_LOC_TEMPLATE)
        ord_loc = ord_loc_template.render(dict_item=ord_dict)
        file.write(ord_loc)
        print(f'Ordinal namelist localization file written to {ord_loc_file}')


def create_seq_key(key, value, id):
    ord = re.search(r'\$\S\$', value).group().replace('$', '')
    ord_base = "".join(key.split('_')[1:]).upper()
    return f"{id.upper()}_{ord_base}_{c.ORD_TYPES[ord]}"


def csv_to_dicts(namelist_csv):
    namelist_dict = {key: [] for key in get_template_variables()}
    with open(namelist_csv, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            for k, v in row.items():
                if k in namelist_dict.keys() and len(v) > 0:
                    qv = (f'\"{v}\"' if 'namelist' not in k else v)
                    namelist_dict[k].append(qv)

    processed_dict = {key: " ".join(value) for key, value in namelist_dict.items()}
    ord_dict = OrderedDict()
    for k, v in processed_dict.items():
        if "$" in v:
            seq_key = create_seq_key(k, v, namelist_dict['namelist_id'][0])
            ord_dict[seq_key] = v
            processed_dict[k] = seq_key
    return processed_dict, ord_dict


def get_template_variables():
    variables = jinja2schema.infer(Path(os.path.join(c.TEMPLATES_DIR, "namelist.txt")).read_text())
    meta_list = ['namelist_title', 'namelist_author', 'namelist_id']
    objects = []
    for category in variables.items():
        if category[0] not in meta_list:
            objects.append(category[0])
    objects.sort()
    meta_list.extend(objects)
    return meta_list


def csv_template(args):
    fields = get_template_variables()
    file_dest = f'{args.dump_csv_template.rstrip(".csv")}.csv'
    with open(file_dest, 'w', newline='\n') as file:
        writer = csv.writer(file)
        writer.writerow(fields)
        print(f'Blank CSV template written to {file_dest}')


def main():
    args = parser.parse_args()
    if args.dump_csv_template:
        csv_template(args)
    else:
        create_mod(args)


parser = argparse.ArgumentParser(
    description='A tool for creating Stellaris namelist mods from a CSV file',
    usage='namelist_generator.py -c [NAMELIST_FILE]',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-c', '--namelist_csv', help="path to the namelist csv file", required=False)
parser.add_argument('-m', '--mod_name', help="name to use for the generated mod", required=False)
parser.add_argument('-d', '--dump_csv_template', help='dump a blank csv with namelist headers with the specified name',
                    required=False)

if __name__ == "__main__":
    sys.exit(main())
