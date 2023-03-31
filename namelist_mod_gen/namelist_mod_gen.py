import argparse
import datetime
import os
import sys

from jinja2 import Environment, FileSystemLoader

import constants.constants as c
from file_handlers.csv import csv_template, csv_to_dicts
from file_handlers.paths import nl_csv_files, make_mod_directories
from file_handlers.writers import write_common_namelist
from execution.execute import executor
from localisation.localisation import localise_namelist, localise_descriptor
from nmg_logging.logger import Logger
from validation.validation import pi_validate
from clean.cleaner import clean_input_text

parser = argparse.ArgumentParser()
parent_parser = argparse.ArgumentParser(
    description='A tool for creating optionally translated Stellaris namelist mods from a CSV file',
    usage='namelist_generator.py [MODE:mod or csv] [path/to/output/dir] -n [/path/to/csv/dir] [OPTIONAL_ARGS]',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
sub = parser.add_subparsers(dest='cmd')

namelist = sub.add_parser(name='mod',
                          description='Produce namelists from an a directory containing csv files',
                          usage='tbd',
                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
namelist.add_argument('mod_output_dir', help='Full path to the mod output directory')
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
    mod_dirs = make_mod_directories(args.mod_name, args.mod_output_dir)

    # This should be the input to all downstream functions
    namelist_master = {
        'directories': mod_dirs,
        'template': template_env.get_template(c.NAMELIST_TEMPLATE),
        'namelists': {''.join(nl['namelist_id']): {'data': nl} for nl in namelist_sources},
        'overwrite': args.overwrite
    }

    # Write the common namelist files using the master dictionary
    executor(func=write_common_namelist, namelists=namelist_master, parallel_process=args.parallel)

    # Write the basic localisation files using the master dictionary
    namelist_master['template'] = template_env.get_template(c.NAMELIST_LOC_TEMPLATE)
    executor(func=localise_namelist, namelists=namelist_master, parallel_process=args.parallel)

    # Write the localisation descriptor files using the master dictionary
    namelist_master['template'] = template_env.get_template(c.NAMELIST_DEF_TEMPLATE)
    namelist_master['author'] = args.author
    executor(func=localise_descriptor, namelists=namelist_master, parallel_process=args.parallel)


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
