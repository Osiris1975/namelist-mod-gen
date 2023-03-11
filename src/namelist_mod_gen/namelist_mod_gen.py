#!/usr/bin/env python

import argparse
import constants as c
import copy
import csv
import io
from jinja2 import Environment, FileSystemLoader
import jinja2schema
import os
from random import shuffle, choice
import shutil
import sys
import sqlite3
import translators as ts
import translators.server as tss
import re
from pathlib import Path
from string import printable
from collections import Counter
from difflib import get_close_matches
from multiprocessing import Pool
import logging

logging.basicConfig(level=logging.DEBUG)
template_loader = FileSystemLoader(searchpath=c.TEMPLATES_DIR)
template_env = Environment(loader=template_loader)


con = sqlite3.connect("translations.db")
cur = con.cursor()


def insert(txt, translation, lang_code):
    long_lang = c.LANGUAGES[lang_code]
    src_text = f"\042{txt.replace('$', '_')}\042"
    trans_text = f"\042{translation.replace('$', '_')}\042"
    query = f"INSERT OR IGNORE INTO {long_lang} (english, {long_lang}) VALUES({src_text}, {trans_text});"
    cur.execute(query)
    con.commit()


def check_in_db(txt, to_lang):
    query = f"CREATE TABLE IF NOT EXISTS {c.LANGUAGES[to_lang]} (english varchar, {c.LANGUAGES[to_lang]} varchar, UNIQUE(english))"
    cur.execute(query)
    txt = txt.replace("'", "''")
    lookup = f"SELECT {c.LANGUAGES[to_lang]} FROM {c.LANGUAGES[to_lang]} where english='{txt}'"
    logging.debug(f'Execution query:\n {lookup}')
    res = cur.execute(lookup)
    translation = res.fetchone()
    if translation:
        return translation[0].replace(' •', '')
    else:
        return ''


def validate_translation(trans_array, original_txt, count):
    if count == 3:
        logging.warning(
            f'Could not find a best match for {original_txt} from list: {trans_array}. Using original text.')
        return original_txt
    matches = get_close_matches(original_txt, trans_array)
    if len(matches) > 0:
        return matches[0].replace(' •', '')
    occurence_count = Counter(trans_array)
    counts = sorted(occurence_count.values())
    ct_array = [len(occurence_count.most_common(1)[0][0].split(' ')), len(original_txt.split(' '))]
    ct_array.sort()
    if counts[-1] > 1 and ct_array[1] - ct_array[0] < 2:
        return occurence_count.most_common(1)[0][0]
    else:
        return validate_translation(trans_array, trans_array[0], count + 1)


def translate(txt, to_lang):
    if txt == '':
        return txt
    token = ''
    if '$' in txt:
        token = re.match(r'\$\S+\$', txt).group()
        txt = txt.replace(token, '_')
    translator_pool = copy.copy(tss.translators_pool)
    shuffle(translator_pool)
    removed = []
    translated = check_in_db(txt, to_lang)
    if translated:
        return translated.replace('_', token)
    else:
        for translator in translator_pool:
            logging.debug(f'Current translator pool {translator_pool}')
            try:
                trans_array = [ts.translate_text(txt, translator, from_language='en', to_language=to_lang).title()]
                for i in range(0, 2):
                    trans_array.append(ts.translate_text(txt, choice(translator_pool),
                                                         from_language='en',
                                                         to_language=to_lang).title().replace(' •', ''))
                translated = validate_translation(trans_array, txt)
                logging.debug(f'Translation completed with {translator}.')
                insert(txt, translated, to_lang)
                translator_pool = copy.copy(tss.translators_pool)
                break
            except Exception as e:
                logging.error(f'Translation exception: {e}')
                removed.append(translator)
                translator_pool.remove(translator)
                if len(translator_pool) > 2:
                    logging.debug(f'Translation of {txt} failed using {translator} with {e} Trying another one from list: {translator_pool}')
                else:
                    logging.info(f'Ran out of translator options. Resetting the translator pool.')
                    translator_pool = copy.copy(tss.translators_pool)
        if not translated:
            translated = ''
        return translated.replace('_', token)


def translate_dict(indict, to_lang_code):
    translated_dict = dict()
    for k, v in indict.items():
        logging.debug(f'Attempting to translate {k}: {v} to {to_lang_code}')
        translation = translate(v, to_lang_code)
        translated_dict[k] = translation.title()
    return translated_dict


def make_mod_directories(mod_name):
    dirs = {
        "namelist": os.path.join(c.MOD_OUTPUT_DIR, mod_name, 'common', 'name_lists'),
        "localization": [os.path.join(c.MOD_OUTPUT_DIR, mod_name, 'localisation', lang, 'name_lists') for lang in
                         c.LANGUAGES.values()]
    }
    if os.path.exists(dirs["namelist"]):
        shutil.rmtree(dirs["namelist"])
    os.makedirs(dirs["namelist"])

    for d in dirs['localization']:
        if os.path.exists(d):
            shutil.rmtree(d)
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


def create_mod(args):
    mod_dirs = make_mod_directories(args.mod_name)
    csv_files = abs_file_paths(args.namelists)
    namelist_info = {}

    for f in csv_files:
        if 'DS_Store' in f:
            continue
        nl_dict = csv_to_dicts(f, args.author.lower())
        namelist_info[nl_dict['namelist_id'][0]] = {
            'file': f,
            'author': args.author,
            'title': nl_dict['namelist_title'][0]
        }

        # Generate namelist file for each list
        name_list_file = os.path.join(mod_dirs["namelist"], f"{nl_dict['namelist_id'][0]}.txt")
        with io.open(name_list_file, 'w', encoding='utf-8-sig') as file:
            namelist_template = template_env.get_template(c.NAMELIST_TEMPLATE)
            render_dict = {k: " ".join(v) for k, v, in nl_dict.items()}
            name_list = namelist_template.render(render_dict)
            file.write(name_list)
            logging.info(f'Namelist file written to {name_list_file}')

        # Generate ord localization files for each name list
        for dir in mod_dirs['localization']:
            lang = dir.split('/')[-2]
            lang_code = list(c.LANGUAGES.keys())[list(c.LANGUAGES.values()).index(lang)]
            ord_loc_file = os.path.join(dir, f"name_list_{nl_dict['namelist_id'][0].upper()}_l_{lang}.yml")
            loc_dict = make_loc_dict(nl_dict)
            if lang != 'english':
                try:
                    loc_dict = translate_dict(loc_dict, lang_code)
                except Exception as e:
                    logging.error(f'Translation failure: {e}')
                    con.close()
                    sys.exit(1)

            with io.open(ord_loc_file, 'w', encoding='utf-8-sig') as file:
                quotified = {k: f'\"{v}\"' for k, v in loc_dict.items()}
                namelist_loc_template = template_env.get_template(c.NAMELISTS_LOC_TEMPLATE)
                nl_loc = namelist_loc_template.render(dict_item=quotified, lang=lang)
                file.write(nl_loc)
                logging.info(f'Namelist localization file written to {ord_loc_file}')

            # generate localization files
            namelist_loc_file = os.path.join(dir, f"{args.author.lower()}_namelist_l_{lang}.yml")
            nl_loc_template = template_env.get_template(c.NL_TITLES_LOC_TEMPLATE)

            with io.open(namelist_loc_file, 'w', encoding='utf-8') as file:
                if lang != 'english':
                    id = nl_dict['namelist_id'][0]
                    namelist_info[id]['title'] = translate(namelist_info[id]['title'], lang_code)
                nl_loc = nl_loc_template.render(dict_item=namelist_info, lang=lang)

                file.write(nl_loc)
                logging.info(f'Namelist info localization file written to {namelist_loc_file}')


def create_seq_key_dict(key, values, author, namelist_id):
    if len(values) > 1:
        value_keys = [f'{author.upper()}_{namelist_id.upper()}_{key.upper()}_{vkey.upper()}' for vkey in values]
        value_keys = [vkey.replace("'", "") for vkey in value_keys]
        return dict(zip(value_keys, values))
    else:
        return {f"{author.upper()}_{namelist_id.upper()}_{key.upper()}": values}


def clean(txt):
    logging.debug(f'Cleaning txt {txt}...')
    cleaned = ''.join(char for char in txt if char in printable).strip()
    return cleaned


def csv_to_dicts(namelists, author):
    namelist_dict = {key: [] for key in get_template_variables()}
    with open(namelists, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            for k, v in row.items():
                if k in namelist_dict.keys() and len(v) > 0:
                    # qv = (f'\"{v}\"' if 'namelist' not in k else v)
                    namelist_dict[k].append(clean(v))

    namelist_id = namelist_dict['namelist_id'][0]
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
        logging.info(f'Blank CSV template written to {file_dest}')


def main():
    args = parser.parse_args()
    if args.dump_csv_template:
        csv_template(args)
    else:
        create_mod(args)
        con.close()


parser = argparse.ArgumentParser(
    description='A tool for creating Stellaris namelist mods from a CSV file',
    usage='namelist_generator.py -c [NAMELIST_FILE]',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-c', '--namelists', help="path to the directory with namelist csv files", required=False)
parser.add_argument('-a', '--author', help="mod author", required=False)
parser.add_argument('-m', '--mod_name', help="name to use for the generated mod", required=False)
parser.add_argument('-d', '--dump_csv_template', help='dump a blank csv with namelist headers with the specified name',
                    required=False)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        con.close()
        logging.error(f"Process failed with {e}")

# TODO: For localization, need to resolve issue where tokens get moved. Maybe based on token put in an example word
# based on what kind of token it is (first for $ORD$, I for $R$ and 1 for $C$). Then replace example token before writing.
# TODO: namelist file with titles are all in korean.
# TODO: Once that's resolved, need to use localization keys for all other fields for full translated localization.
