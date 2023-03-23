#!/usr/bin/env python

import argparse
import csv
import datetime
import io
import logging
import os
import re
import shutil
import sqlite3
import sys
from multiprocessing import Pool
from pathlib import Path
from string import printable

import colorlog
import jinja2schema
from jinja2 import Environment, FileSystemLoader

from constants import constants as c
from translation.translation import translate_dict, translate
from validation.validation import validate

try:
    loglevel = os.getenv('LOG_LEVEL').upper()
except AttributeError:
    loglevel = 'INFO'

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s[%(asctime)s][%(levelname)s][%(name)s]: %(message)s'))
file_handler = logging.FileHandler(
    filename=f"{c.PROJECT_DIR}/logs/{datetime.datetime.now().strftime('%d.%m.%Y_%H.%M.%S')}.main.log")
file_handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s][%(name)s]: %(message)s'))
file_handler.setLevel(loglevel)

logger = colorlog.getLogger('__main__.' + __name__)
logger.addHandler(handler)
logger.setLevel(loglevel)
logger.addHandler(file_handler)

template_loader = FileSystemLoader(searchpath=c.TEMPLATES_DIR)
template_env = Environment(loader=template_loader)

create_table_connection = sqlite3.connect("translations.db", timeout=15)

process_dirs = []


def make_mod_directories(mod_name):
    dirs = {
        "namelist": os.path.join(c.MOD_OUTPUT_DIR, mod_name, 'common', 'name_lists'),
        "localisation": [os.path.join(c.MOD_OUTPUT_DIR, mod_name, 'localisation', lang, 'name_lists') for lang in
                         c.LANGUAGES.values()]
    }
    if not os.path.exists(dirs["namelist"]):
        os.makedirs(dirs["namelist"])

    for d in dirs['localisation']:
        if not os.path.exists(d):
            os.makedirs(d)

    return dirs


def abs_file_paths(directory):
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f))


def make_loc_dict(indict):
    loc_dict = dict()
    for k, v in indict.items():
        if type(v) == dict:
            for k2, v2 in v.items():
                if type(v2) == list:
                    if len(v2) == 0:
                        loc_dict[k2] = ""
                    else:
                        loc_dict[k2] = v2[0]
                else:
                    loc_dict[k2] = v2
    return loc_dict


def create_localized_namelist_listing(input, author, root_loc_dir):
    nl_def_template = template_env.get_template(c.NL_DEF_TEMPLATE)

    for code, lang in c.LANGUAGES.items():
        def_dict = dict()
        for nl, info in input.items():
            if code != 'en':
                title = translate(None, info['title'], code, reader=create_table_connection, writer=create_table_connection, begin=False)[1]
            else:
                title = info['title']
            def_dict[nl] = {
                'title': title.replace('(onl)', '(ONL)').replace('(Onl)', '(ONL)')
            }

        nl_def_file = os.path.join(root_loc_dir, lang, f"name_lists/{author.lower()}_namelist_l_{lang}.yml")
        try:
            if not os.path.exists(nl_def_file):
                with io.open(nl_def_file, 'w', encoding='utf-8') as file:
                    nl_loc = nl_def_template.render(dict_item=def_dict, author=author, lang=lang)
                    file.write(nl_loc)
                    logger.info(f'Localized namelist description file written to {nl_def_file}')
            else:
                logger.warning(f'File already exists:{nl_def_file}. Skipping...')
        except Exception as e:
            logger.error(f'Failed to create {nl_def_file}: {e}')


def create_localized_translations_mapped(inputs):
    create_localized_translations(inputs, True)


def create_localized_translations(loc_inputs, translate):
    logger.info(f"PROCESSING NAMELIST {loc_inputs['data']['namelist_title'][0]}")
    loc_dir = loc_inputs['dir']
    nl_dict = loc_inputs['data']
    lang = loc_dir.split('/')[-2]
    lang_code = list(c.LANGUAGES.keys())[list(c.LANGUAGES.values()).index(lang)]
    ord_loc_file = os.path.join(loc_dir, f"name_list_{nl_dict['namelist_id'][0].upper()}_l_{lang}.yml")
    if not os.path.exists(ord_loc_file):
        loc_dict = make_loc_dict(nl_dict)
        if lang != 'english':
            loc_dict = translate_dict(loc_dict, lang_code, translate)
        with io.open(ord_loc_file, 'w', encoding='utf-8-sig') as file:
            quotified = {k: f'\"{v}\"' for k, v in loc_dict.items()}
            namelist_loc_template = template_env.get_template(c.NL_LOC_TEMPLATE)
            nl_loc = namelist_loc_template.render(dict_item=quotified, lang=lang)
            file.write(nl_loc)
            logger.info(f'Namelist localisation file written to {ord_loc_file}')
    else:
        logger.warning(f'File already exists:{ord_loc_file}. Skipping...')


def create_mod(args):
    if args.translate:
        # cur = create_table_connection.cursor()
        # for lang in c.LANGUAGES.values():
        #     if lang != 'english':
        #         # run some initial queries
        #         queries = [
        #             f"CREATE TABLE IF NOT EXISTS {lang} (english varchar, {lang} varchar, translators varchar, is_translated boolean, is_same boolean, UNIQUE(english))",
        #             f"delete from {lang} where {lang} like '%(%';",
        #             f"delete from {lang} where {lang} like '%:%';",
        #             f"delete from {lang} where length({lang}) > 50;"
        #         ]
        #         for q in queries:
        #             cur.execute(q)
        pass
    mod_dirs = make_mod_directories(args.mod_name)
    csv_files = abs_file_paths(args.namelists)
    namelist_info = dict()
    ld = ''
    for f in csv_files:
        if 'DS_Store' in f:
            continue
        nl_dict = csv_to_dicts(f, args.author.lower())
        namelist_info[nl_dict['namelist_id'][0]] = {
            'file': f,
            'title': nl_dict['namelist_title'][0],
            'source_data': nl_dict
        }

        # Create output file names and skip if all three exist:
        name_list_file = os.path.join(mod_dirs["namelist"], f"{nl_dict['namelist_id'][0]}.txt")

        if not os.path.exists(name_list_file):
            # Generate namelist file for each list
            with io.open(name_list_file, 'w', encoding='utf-8-sig') as file:
                namelist_template = template_env.get_template(c.NAMELIST_TEMPLATE)
                render_dict = {k: " ".join(v) for k, v, in nl_dict.items()}
                name_list = namelist_template.render(render_dict)
                file.write(name_list)
                logger.info(f'Namelist file written to {name_list_file}')

        # Generate translated localisation files for each name list
        inputs = []

        for loc_dir in mod_dirs['localisation']:
            input = {
                'dir': loc_dir,
                'data': nl_dict,
                'meta': namelist_info,
                'author': args.author,
                'translate': True
            }
            inputs.append(input)
            ld = loc_dir

        if args.multiprocess:
            with Pool(os.cpu_count() - 1) as pool:
                pool.map(create_localized_translations_mapped, inputs)
                pool.join()
                logger.info(f'------------------ALL TASKS DONE------------------')
        else:
            for i in inputs:
                create_localized_translations(i, args.translate)

        # generate namelist description file for each language

    loc_split = ld.split('/')
    root_loc_dir = os.path.join('/', *loc_split[0:-2])
    # create_localized_namelist_listing(namelist_info, args.author, root_loc_dir)


def create_seq_key_dict(key, values, author, namelist_id):
    try:
        if len(values) > 1:
            vdict = dict()
            for v in values:
                value_key = f'{author}_{namelist_id}_{key}_{v}'
                value_key = re.sub('[^0-9a-zA-Z]+', '_', value_key).upper()
                vdict[value_key] = v
            return vdict
        else:
            value_key = re.sub('[^0-9a-zA-Z]+', '_', key).upper()
            return {f"{author.upper()}_{namelist_id.upper()}_{value_key}": values}
    except Exception as e:
        logger.error(f'Failed creating sequence keys: {e}')


def clean(txt):
    logger.debug(f'Cleaning txt {txt}...')
    cleaned = ''.join(char for char in txt if char in printable).strip()
    return cleaned


def csv_to_dicts(namelists, author):
    namelist_dict = {key: [] for key in get_template_variables()}
    with open(namelists, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            for k, v in row.items():
                if k in namelist_dict.keys() and len(v) > 0:
                    namelist_dict[k].append(clean(v))

    errors = []
    for v in namelist_dict.values():
        if len(v) > 0:
            errors.extend(validate(v[0]))

    namelist_id = namelist_dict['namelist_id'][0]
    if len(errors) > 0:
        errors_string = '\n'.join(errors)
        logger.critical(f'Namelist {namelist_id} has incompatible names: {errors_string}')
        sys.exit(1)
    for k, v in namelist_dict.items():
        if k not in c.UNKEYED_FIELDS:
            values = create_seq_key_dict(k, v, author, namelist_id)
            namelist_dict[k] = values
    return namelist_dict


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
        logger.info(f'Blank CSV template written to {file_dest}')


def main():
    args = parser.parse_args()
    logger.warning(f'TRANSLATION ENABLED: This can take a long time...')
    if args.dump_csv_template:
        csv_template(args)
    else:
        st = datetime.datetime.now()
        create_mod(args)
        et = datetime.datetime.now()
        elapsed_time = et - st
        logger.info(f'NAMELIST MOD GENERATION COMPLETED IN {elapsed_time}.')


parser = argparse.ArgumentParser(
    description='A tool for creating optionally translated Stellaris namelist mods from a CSV file',
    usage='namelist_generator.py -c [NAMELIST_FILE]',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-n', '--namelists', help="path to the directory with namelist csv files", required=False)
parser.add_argument('-a', '--author', help="mod author", required=False)
parser.add_argument('-m', '--mod_name', help="name to use for the generated mod", required=False)
parser.add_argument('-M', '--multiprocess', default=False, help='experimental: activate multiprocessing mode',
                    action='store_true')
parser.add_argument('-t', '--translate', default=False, help='activate namelist translation', action='store_true')
parser.add_argument('-d', '--dump_csv_template', help='dump a blank csv with namelist headers with the specified name',
                    required=False)

if __name__ == "__main__":
    sys.exit(main())
