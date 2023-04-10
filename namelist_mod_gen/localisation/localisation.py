import logging
import os
import traceback as tb

import constants.constants as c
from file_handlers.writers import write_template, ok_to_overwrite
from translation.translate import Translator

log = logging.getLogger('NMG')


def quotify(txt_dict):
    return {k: f'\"{v}\"' for k, v in txt_dict.items()}


def localise_namelist(namelist):
    for lang in c.LANGUAGES.values():
        loc_dir = None
        for d in namelist['directories']['localisation']:
            if c.PARADOX_LANGUAGES[lang] in d:
                loc_dir = d
                break

        dest_file = os.path.join(loc_dir, f"name_list_{namelist['id'].upper()}_l_{c.PARADOX_LANGUAGES[lang]}.yml")
        if not ok_to_overwrite(namelist, dest_file):
            continue

        loc_dict = make_loc_dict(namelist['data'])
        if namelist['translate'] and lang != 'english':
            try:
                t = Translator(loc_dict, lang, namelist['id'], namelist['available_apis'])
                t.run()
                loc_dict = t.translated_dict

            except Exception as e:
                log.error(f'Translation problem: {e}: {tb.format_exc()}')

        if not loc_dict:
            log.critical(f'Localisation dictionary should not be empty for {namelist["id"]} after {lang} translation.')
            raise ValueError(
                f'Localisation dictionary should not be empty for {namelist["id"]} after {lang} translation.')
        quotified = quotify(loc_dict)
        write_template(
            render_dict=quotified,
            dest_file=dest_file,
            template=namelist['template'],
            lang=c.PARADOX_LANGUAGES[lang],
            encoding='utf-8-sig'
        )


def localise_descriptor(namelist):
    for loc_dir in namelist['directories']['localisation']:
        dir_lang = loc_dir.split(os.sep)[-2]
        trans_lang = dir_lang.replace('braz_por', 'portuguese').replace('simp_chinese', 'chinese')
        titles = {k: v['data']['namelist_title'][0] for k, v in namelist['namelists'].items()}

        if namelist['translate'] and dir_lang != 'english':
            t = Translator(
                namelist=titles,
                lang=trans_lang,
                namelist_id=f'titles_{namelist["id"]}',
                available_apis=namelist['available_apis']
            )
            t.run()
            titles = t.translated_dict

        dest_file = f"{namelist['author'].lower()}_namelist_l_{dir_lang}.yml"
        dest_file = os.path.join(loc_dir, dest_file)

        write_template(
            render_dict=titles,
            dest_file=dest_file,
            template=namelist['template'],
            lang=dir_lang,
            author=namelist['author'],
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
