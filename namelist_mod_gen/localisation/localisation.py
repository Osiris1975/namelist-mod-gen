import copy
import logging
import os

import constants.constants as c
from file_handlers.writers import write_template

log = logging.getLogger('NMG')


def quotify(txt_dict):
    return {k: f'\"{v}\"' for k, v in txt_dict.items()}


def localise_namelist(namelist):
    loc_dict = make_loc_dict(namelist['data'])
    quotified = quotify(loc_dict)
    lang_copy = copy.copy(c.LANGUAGES)
    langs = list(lang_copy.values())
    for loc_dir in namelist['directories']['localisation']:
        for lang in langs:
            dest_file = os.path.join(loc_dir, f"name_list_{namelist['id'].upper()}_l_{lang}.yml")
            if lang in loc_dir:
                write_template(
                    render_dict=quotified,
                    dest_file=dest_file,
                    template=namelist['template'],
                    lang=lang,
                    encoding='utf-8-sig'
                )
                langs.remove(lang)
                break


def localise_descriptor(namelist):

    titles = {k: v['data']['namelist_title'][0] for k, v in namelist['data'].items()}
    for k, v in namelist['namelists'].items():
        titles[k] = v['data']['namelist_title'][0]

    for loc_dir in namelist['directories']['localisation']:
        lang = loc_dir.split(os.sep)[-2]
        dest_file = f"{namelist['author'].lower()}_namelist_l_{lang}.yml"
        dest_file = os.path.join(loc_dir, dest_file)

        write_template(
            render_dict=titles,
            dest_file=dest_file,
            template=namelist['template'],
            lang=lang,
            encoding='utf-8'
        )


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
