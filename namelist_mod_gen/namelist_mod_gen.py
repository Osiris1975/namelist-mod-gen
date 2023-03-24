import argparse
import datetime
import os
import sys

from nmg_logging.logger import Logger

try:
    loglevel = os.getenv('LOG_LEVEL').upper()
except AttributeError:
    loglevel = 'INFO'

log_path = os.path.dirname
logger = Logger('Main', loglevel).add_file_handler(log_path).get_logger()




parser = argparse.ArgumentParser(
    description='A tool for creating optionally translated Stellaris namelist mods from a CSV file',
    usage='namelist_generator.py -c [NAMELIST_FILE]',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
sub = parser.add_subparsers()

namelist = sub.add_parser(name='namelist',
                          description='Produce namelists from an a directory containing csv files',
                          usage='tbd',
                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
namelist.add_argument('-n', '--namelists', help="path to the directory with namelist csv files", required=False)
namelist.add_argument('-a', '--author', help="mod author", required=False)
namelist.add_argument('-m', '--mod_name', help="name to use for the generated mod", required=False)
namelist.add_argument('-M', '--multiprocess', default=False, help='experimental: activate multiprocessing mode',
                      action='store_true')
namelist.add_argument('-t', '--translate', default=False, help='activate namelist translation', action='store_true')

csv = sub.add_parser(name='csv',
                     description='Create a CSV template or convert an existing namelist mod to CSV',
                     usage='tbd',
                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

csv.add_argument('-d', '--dump_csv_template', help='dump a blank csv with namelist headers with the specified name',
                 required=False)
csv.add_argument('-c', '--convert', help='Convert a mod in the given directory into a CSV file.', required=False)


def main():
    st = datetime.datetime.now()
    args = parser.parse_args()
    logger.info(f'NMG Started in {""} mode at{st}')

    et = datetime.datetime.now()


if __name__ == "__main__":
    sys.exit(main())
