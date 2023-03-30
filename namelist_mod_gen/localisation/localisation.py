import copy
import logging
import os

import constants.constants as c
from file_handlers.writers import write_template

log = logging.getLogger('NMG')


def quotify(txt_dict):
    return {k: f'\"{v}\"' for k, v in txt_dict.items()}


def localise_namelist(name_list):
    loc_dict = make_loc_dict(name_list['data'])
    quotified = quotify(loc_dict)
    lang_copy = copy.copy(c.LANGUAGES)
    langs = list(lang_copy.values())
    for loc_dir in name_list['directories']['localisation']:
        for lang in langs:
            dest_file = os.path.join(loc_dir, f"name_list_{name_list['id'].upper()}_l_{lang}.yml")
            if lang in loc_dir:
                write_template(quotified, dest_file, name_list['localisation_template'], lang)
                langs.remove(lang)
                break


def make_loc_dict(namelist):
    loc_dict = dict()
    for k, v in namelist.items():
        if type(v) == dict:
            for k2, v2 in v.items():
                if type(v2) == list:
                    loc_dict[k2] = v2[0]
                else:
                    loc_dict[k2] = v2
    return loc_dict
