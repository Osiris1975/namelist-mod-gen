import logging
import os
from csv import Sniffer
import traceback

import constants.constants as c

logger = logging.getLogger('NMG')


def nl_csv_files(directory):
    """
    Given a directory, yield csv files from it.
    :param directory: location where the csv files are stored.
    :return:
    """
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            try:
                path = os.path.join(dirpath, f)
                with open(path) as csv_file:
                    sniff = Sniffer().sniff(csv_file.read(1024))
                    if sniff and f[-4:] == '.csv':
                        yield os.path.abspath(os.path.join(dirpath, f))
            except UnicodeDecodeError:
                tb = traceback.format_exc()
                logger.warning(f'{f} is not a recognized CSV file, skipping it\n{tb}')


def make_mod_directories(mod_name, root_dir):
    """
    Creates the mod directories required for the mod to work
    :param root_dir: the root directory for the mod
    :param mod_name: mod name as passed in at command line
    :return:
    """
    dirs = {
        "common": os.path.join(root_dir, mod_name, 'common', 'name_lists'),
        "localisation": [os.path.join(root_dir, mod_name, 'localisation', lang, 'name_lists') for lang in
                         c.PARADOX_LANGUAGES.values()]
    }
    if not os.path.exists(dirs["common"]):
        os.makedirs(dirs["common"])

    for d in dirs['localisation']:
        if not os.path.exists(d):
            os.makedirs(d)

    return dirs
