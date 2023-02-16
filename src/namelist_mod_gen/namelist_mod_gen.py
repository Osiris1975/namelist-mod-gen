#!/usr/bin/env python

import argparse
import constants as c
import csv
from jinja2 import Environment, FileSystemLoader
import jinja2schema
import os
import sys
from pathlib import Path

template_loader = FileSystemLoader(searchpath=c.TEMPLATES_DIR)
template_env = Environment(loader=template_loader)
namelist_template = template_env.get_template(c.NAMELIST_TEMPLATE)


def render(args):
    namelist_dict = {key: [] for key in get_template_variables()}
    with open(args.namelist_csv, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            for k, v in row.items():
                if k in namelist_dict.keys() and len(v) > 0:
                    qv = (f'\"{v}\"' if 'namelist' not in k else v)
                    namelist_dict[k].append(qv)
    namelist_dict2 = {key: " ".join(value) for key, value in namelist_dict.items()}
    file_dest = os.path.join(c.NAME_LIST_OUTPUT_DIR, f"{namelist_dict2['namelist_id']}.txt")
    with open(file_dest, 'w') as file:
        template_string = namelist_template.render(namelist_dict2)
        file.write(template_string)
        print(f'Namelist file written to {file_dest}')


def get_template_variables():
    variables = jinja2schema.infer(Path(os.path.join(c.TEMPLATES_DIR, "namelist.txt")).read_text())
    variables_list = ['namelist_title', 'namelist_author', 'namelist_id']
    objects = []
    for category in variables.items():
        objects.append(category[0])
    objects.sort()
    variables_list.extend(objects)
    return variables_list


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
        render(args)


parser = argparse.ArgumentParser(
    description='A tool for creating Stellaris namelists and namelist mods from a CSV file and CLI arguments',
    usage='namelist_generator.py [NAMELIST_FILE]',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-c', '--namelist_csv', help="path to the namelist csv file", required=False)
parser.add_argument('-n', '--name_list_title', help="Title for the namelist txt file", required=False)
parser.add_argument('-a', '--author', help="Namelist author to add to txt file", required=False)
parser.add_argument('-d', '--dump_csv_template', help='dump a blank csv with namelist headers with the specified name',
                    required=False)

if __name__ == "__main__":
    sys.exit(main())
