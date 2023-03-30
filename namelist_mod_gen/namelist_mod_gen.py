import argparse
import datetime
import os
import sys

from jinja2 import Environment, FileSystemLoader

import constants.constants as c
from db.db import Connection
from file_handlers.csv import csv_template, csv_to_dicts
from file_handlers.paths import nl_csv_files, make_mod_directories
from gen.generate import generate, write_common_namelist
from localisation.localisation import localise_namelist
from nmg_logging.logger import Logger
from validation.validation import pi_validate

parser = argparse.ArgumentParser()
parent_parser = argparse.ArgumentParser(
    description='A tool for creating optionally translated Stellaris namelist mods from a CSV file',
    usage='namelist_generator.py -n [NAMELIST_FILE]',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
sub = parser.add_subparsers(dest='cmd')

namelist = sub.add_parser(name='mod',
                          description='Produce namelists from an a directory containing csv files',
                          usage='tbd',
                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
namelist.add_argument('-n', '--namelists', help="path to the directory with namelist csv files", required=False)
namelist.add_argument('-a', '--author', help="mod author", required=False)
namelist.add_argument('-m', '--mod_name', help="name to use for the generated mod", required=False)
namelist.add_argument('-p', '--parallel', default=False,
                      help='experimental: activate parallel processing mode to speed up mod generation',
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


def execute_mod(args, db):
    # Gather CSV files from directory
    csv_files = nl_csv_files(args.namelists)

    # CSV File Handler ingests the csv files and converts them to dictionaries
    namelist_sources = [csv_to_dicts(f, args.author) for f in csv_files]

    # Check for errors
    errors = []
    for nd in namelist_sources:
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

    # This should be the input to all downstream functions
    namelist_master = {
        'directories': mod_dirs,
        'namelist_template': template_env.get_template(c.NAMELIST_TEMPLATE),
        'localisation_template':  template_env.get_template(c.NL_LOC_TEMPLATE),
        'namelists': {''.join(nl['namelist_id']): {'data': nl} for nl in namelist_sources},
        'overwrite': args.overwrite
    }

    # Write the common namelist files using tne master dictionary
    generate(func=write_common_namelist, name_lists=namelist_master, parallel_process=args.parallel)

    # Write the basic localisation files using the master dictionary
    generate(func=localise_namelist, name_lists=namelist_master, parallel_process=args.parallel)
    print()
    # Translation for the localization files
    # for nl in namelist_sources:
    #     loc_input = {
    #         'language_dicts': language_dicts,
    #         'namelist_data': nl,  # the namelist data
    #         'loc_dirs': mod_dirs['localisation']
    #     }
    #     loc_inputs.append(loc_input)
    #
    #
    #
    # inputs = []
    # for loc_dir in mod_localisation_dirs:
    #     input = {
    #         'dir': loc_dir,
    #         'data': '',
    #         'meta': '',
    #         'author': args.author,
    #         'translate': True
    #     }
    #     inputs.append(input)


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
        if args.translate:
            db = Connection(c.DB_PATH)
        execute_mod(args, c.DB_PATH)
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

    # Initialize template system
    template_loader = FileSystemLoader(searchpath=c.TEMPLATES_DIR)
    template_env = Environment(loader=template_loader)

    # Initialize logging
    logger = Logger('NMG', level=loglevel)
    logger.add_file_handler(c.LOG_DIR)
    log = logger.get_logger()
    sys.exit(main())
