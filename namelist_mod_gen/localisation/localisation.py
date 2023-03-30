import io
import os
import logging
import traceback

import constants.constants as c
from multiprocess.pool import ThreadPool

log = logging.getLogger('NMG')

#TODO: Resume fixing this
def localise_namelist(name_list):
    loc_dict = make_loc_dict(name_list['data'])
    quotified = {k: f'\"{v}\"' for k, v in loc_dict.items()}
    for loc_dir in name_list['directories']['localisation']:
        for lang in c.LANGUAGES.values():
            localisation_file = os.path.join(loc_dir, f"name_list_{name_list['id'].upper()}_l_{lang}.yml")
            with io.open(localisation_file, 'w', encoding='utf-8-sig') as file:
                nl_loc = name_list['localisation_template'].render(dict_item=quotified, lang=lang)
                file.write(nl_loc)
                log.info(f'Namelist localisation file written to {localisation_file}')


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