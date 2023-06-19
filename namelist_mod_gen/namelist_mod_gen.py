import argparse
import datetime
import os
import signal
import sys

from jinja2 import Environment, FileSystemLoader

import constants.constants as c
from execution.execute import executor
from file_handlers.csv import create_template, csv_to_dicts
from file_handlers.paths import nl_csv_files, make_mod_directories
from file_handlers.csv import namelist_txt_to_dict
from file_handlers.writers import write_common_namelist, write_csv_from_dict
from localisation.localisation import localise_namelist, localise_descriptor
from nmg_logging.logger import Logger
from translation.translate import check_api_availability
from validation.validation import pi_validate

parser = argparse.ArgumentParser()
parent_parser = argparse.ArgumentParser(
    description='A tool for creating optionally translated Stellaris namelist mods from a CSV file',
    usage='namelist_mod_gen.py [MODE:mod or csv] <mode options: run namelist_mod_gen.py [MODE] --help for mode specific documentation.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
sub = parser.add_subparsers(dest='cmd')

namelist = sub.add_parser(name='mod',
                          description='Produce namelists from an a directory containing csv files',
                          usage='namelist_generator.py mod </path/to/desired/output/directory> -n </path/to/input/csv/directory> -m <mod_name> -a <author>',
                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
namelist.add_argument('mod_output_dir', help='Full path to the mod output directory')
namelist.add_argument('-n', '--namelists', help="path to the directory with namelist csv files", required=True)
namelist.add_argument('-a', '--author', help="mod author. Must be all lowercase. Use underscores instead of spaces.",
                      required=True)
namelist.add_argument('-m', '--mod_name',
                      help="name to use for the generated mod. Must be all lowercase. Use underscores instead of spaces.",
                      required=True)
namelist.add_argument('-t', '--translate', default=False, required=False, help='activate namelist translation',
                      action='store_true')
namelist.add_argument('-o', '--overwrite', default=False, required=False, help='overwrite existing namelist files',
                      action='store_true')
namelist.add_argument('-i', '--ignore_validation_errors', required=False, default=False,
                      help='If CSV validation errors are found, NMG will report them as warnings and continue execution.',
                      action='store_true')

csv = sub.add_parser(name='csv',
                     description='Create a CSV template or convert an existing namelist mod to CSV',
                     usage='tbd',
                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

csv.add_argument('-d', '--dump', help='dump a blank csv with namelist headers with the specified name',
                 required=False)
csv.add_argument('-c', '--convert', help='given a mod txt file, convert it to a csv for use in NMG', required=False)
csv.add_argument('-a', '--author', help="mod author. Must be all lowercase. Use underscores instead of spaces.",
                 required=True)
csv.add_argument('-i', '--id',
                 help="ID to use for the generated mod. Must be all lowercase. Use underscores instead of spaces.",
                 required=True)
csv.add_argument('-t', '--title',
                 help="Readable title for namelist, enclosed in quotes.",
                 required=True)
csv.add_argument('-o', '--output_file',
                 help="Full path to the desired output file, ending in .csv",
                 required=True)


def execute_mod(**kwargs):
    # Gather CSV files from directory
    args = kwargs['args']
    csv_files = nl_csv_files(args.namelists)

    # CSV File Handler ingests the csv files and converts them to dictionaries
    namelist_sources = [csv_to_dicts(f, args.author) for f in csv_files]

    errors = []
    for nd in namelist_sources:
        for k, v in nd.items():
            if type(v) == list:
                [errors.extend(pi_validate(i, nd['namelist_title'][0])) for i in v if len(v) > 0]
            if type(v) == dict:
                [errors.extend(pi_validate(i[0], nd['namelist_title'][0])) for i in v.values() if len(v) > 0]

    if len(errors) > 0:
        errors_string = "\n".join(errors)
        log.critical(f'Provided namelists have errors:\n{errors_string}')
        if args.ignore_validation_errors:
            log.warning(f'Reported errors ignored, this may cause namelist errors in game!')
        else:
            log.critical(f'Fix the errors above and rerun NMG or use -i/--ignore_validation_errors to process anyway.')
            sys.exit(1)

    # Create the mod directory structure to write files to
    mod_dirs = make_mod_directories(args.mod_name, args.mod_output_dir)

    # This should be the input to all downstream functions

    namelist_master = {
        'directories': mod_dirs,
        'template': template_env.get_template(c.NAMELIST_TEMPLATE),
        'namelists': {''.join(nl['namelist_id']): {'data': nl} for nl in namelist_sources},
        'overwrite': args.overwrite,
        'translate': args.translate
    }

    # Write the common namelist files using the master dictionary
    executor(func=write_common_namelist, namelists_master=namelist_master)

    # Write the basic localisation files using the master dictionary
    namelist_master['template'] = template_env.get_template(c.NAMELIST_LOC_TEMPLATE)

    if args.translate:
        namelist_master['available_apis'] = kwargs['available_apis']
    executor(func=localise_namelist, namelists_master=namelist_master)

    # Write the localisation descriptor files using the master dictionary
    namelist_master['template'] = template_env.get_template(c.NAMELIST_DEF_TEMPLATE)
    namelist_master['author'] = args.author
    executor(func=localise_descriptor, namelists_master=namelist_master)


def convert_txt(args):
    nld = namelist_txt_to_dict(args.convert, args.author, args.title, args.id)
    write_csv_from_dict(args.output_file, nld)


def execute_csv(**kwargs):
    """
    Executes the commands specified in the csv mode subparser. The following keyword args are legal for execute_csv:
    :param dump: absolute path to location where CSV file should be dumped.
    :return:
    """
    args = kwargs.get('args')
    if args.dump:
        create_template(args.dump)
    if args.convert:
        convert_txt(args)


def main():
    st = datetime.datetime.now()
    args = parser.parse_args()
    log.info(f'Started in {args.cmd} mode at{st}')
    available_apis = None
    if 'translate' in args:
        available_apis = check_api_availability()
    if args.cmd == 'mod':
        execute_mod(args=args, available_apis=available_apis)
    if args.cmd == 'csv':
        execute_csv(args=args)
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
    try:
        sys.exit(main())
    except Exception as e:
        log.critical(f'NMG failed: {e}')
        os.killpg(os.getpid(), signal.SIGTERM)
