import argparse
import copy
import datetime
import io
import os
import sys

import constants.constants as c
from file_handlers.csv import csv_template, csv_to_dicts
from file_handlers.paths import nl_csv_files, make_mod_directories
from jinja2 import Environment, FileSystemLoader
from nmg_logging.logger import Logger
from validation.validation import pi_validate
from db.sqlite_connection import Connection

parser = argparse.ArgumentParser()
parent_parser = argparse.ArgumentParser(
    description='A tool for creating optionally translated Stellaris namelist mods from a CSV file',
    usage='namelist_generator.py -c [NAMELIST_FILE]',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
sub = parser.add_subparsers(dest='cmd')

namelist = sub.add_parser(name='mod',
                          description='Produce namelists from an a directory containing csv files',
                          usage='tbd',
                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
namelist.add_argument('-n', '--namelists', help="path to the directory with namelist csv files", required=False)
namelist.add_argument('-a', '--author', help="mod author", required=False)
namelist.add_argument('-m', '--mod_name', help="name to use for the generated mod", required=False)
namelist.add_argument('-M', '--multiprocess', default=False, help='experimental: activate multiprocessing mode',
                      action='store_true')
namelist.add_argument('-t', '--translate', default=False, help='activate namelist translation', action='store_true')
namelist.add_argument('-o', '--overwrite', default=False, help='overwrite existing namelist files',
                      action='store_true')

csv = sub.add_parser(name='csv',
                     description='Create a CSV template or convert an existing namelist mod to CSV',
                     usage='tbd',
                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

csv.add_argument('-d', '--dump', help='dump a blank csv with namelist headers with the specified name',
                 required=False)
csv.add_argument('-c', '--convert', help='Convert a mod in the given directory into a CSV file.', required=False)


def execute_mod(args):
    # Gather CSV files from directory
    csv_files = nl_csv_files(args.namelists)

    # CSV File Handler ingests the csv files and converts them to dictionaries
    nl_dicts = [csv_to_dicts(f, args.author) for f in csv_files]

    # Check for errors
    errors = []
    for nd in nl_dicts:
        for k, v in nd.items():
            if type(v) == list:
                [errors.extend(pi_validate(i)) for i in v if len(v) > 0]
            if type(v) == dict:
                [errors.extend(pi_validate(i[0])) for i in v.values() if len(v) > 0]

    if len(errors) > 0:
        errors_string = "\n".join(errors)
        log.critical(f'Provided namelists have errors:{errors_string}')
        sys.exit(1)

    # Create the mod directory structure to write files to
    mod_dirs = make_mod_directories(args.mod_name, c.MOD_OUTPUT_DIR)
    mod_common_dir = mod_dirs['namelist']

    # Initialize template system
    template_loader = FileSystemLoader(searchpath=c.TEMPLATES_DIR)
    template_env = Environment(loader=template_loader)

    # Write the namelist common files
    for nl in nl_dicts:
        nl_id = nl['namelist_id'][0]
        nl_title = nl['namelist_title'][0]
        nl_output_path = os.path.join(mod_common_dir, f"{nl_id}.txt")
        if args.overwrite:
            try:
                log.warning(f'Overwrite selected for {nl_title}. Removing {nl_output_path}')
                os.remove(nl_output_path)
            except FileNotFoundError:
                log.debug(f'File {nl_output_path} not found.')
        namelist_template = template_env.get_template(c.NAMELIST_TEMPLATE)
        render_dict = {k: " ".join(v) for k, v, in nl.items()}
        for k, v in render_dict.items():
            if 'second_names' in k and len(v) == 0:
                render_dict[k] = '\"\"'

        with io.open(nl_output_path, 'w', encoding='utf-8-sig') as file:
            name_list = namelist_template.render(render_dict)
            file.write(name_list)
            log.info(f'Namelist file written to {nl_output_path}')

    # Prepare for localization
    mod_localisation_dirs = mod_dirs['localisation']
    inputs = []

    db = Connection()
    langs = copy.copy(c.LANGUAGES)
    lang_list = list(langs.values())
    lang_list.remove('english')
    language_dicts = {lang: None for lang in lang_list}
    for lang in lang_list:
        language_dicts[lang] = db.get_language_dict(lang)
    # Iterate over each namelist in nl_dicts
    # TODO: PICKUP WORK HERE
    for nl in nl_dicts:
        print(nl)
        loc_input = {
            'language_dicts': language_dicts,
            'namelist_data': nl,  # the namelist data
            'loc_dirs': mod_dirs['localisation']
        }


    inputs = []
    for loc_dir in mod_localisation_dirs:
        input = {
            'dir': loc_dir,
            'data': '',
            'meta': '',
            'author': args.author,
            'translate': True
        }
        inputs.append(input)
        ld = loc_dir

def execute_csv(args):
    if args.dump:
        file_dest = f'{args.dump.rstrip(".csv")}.csv'
        csv_template(file_dest)
        log.info(f'Template csv file written to {file_dest}')


def main():
    st = datetime.datetime.now()
    args = parser.parse_args()
    log.info(f'Started in {args.cmd} mode at{st}')
    if args.cmd == 'mod':
        execute_mod(args)
    if args.cmd == 'csv':
        execute_csv(args)
    et = datetime.datetime.now()
    elapsed_time = et - st
    log.info(f'Completed processing in {args.cmd} mode in {elapsed_time}')


if __name__ == "__main__":
    try:
        loglevel = os.getenv('LOG_LEVEL').upper()
    except AttributeError:
        loglevel = 'INFO'

    logger = Logger('NMG', level=loglevel)
    logger.add_file_handler(c.LOG_DIR)
    log = logger.get_logger()
    sys.exit(main())
