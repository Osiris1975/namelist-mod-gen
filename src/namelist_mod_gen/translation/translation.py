import copy
import datetime
import logging
import os
import sqlite3
import threading
from collections import Counter
from difflib import get_close_matches
from queue import Queue
from multiprocessing.pool import ThreadPool
from random import choice

import colorlog
import regex
import requests.exceptions
import translators as ts

from src.namelist_mod_gen.constants import constants as c

loglevel = os.getenv('LOG_LEVEL').upper()
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s[%(asctime)s][%(levelname)s][%(name)s]: %(message)s'))
file_handler = logging.FileHandler(
    filename=f"{c.PROJECT_DIR}/logs/{datetime.datetime.now().strftime('%d.%m.%Y_%H.%M.%S')}.translation.log")
file_handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s][%(name)s]: %(message)s'))
file_handler.setLevel(loglevel)

logger = colorlog.getLogger('__main__.' + __name__)
logger.addHandler(handler)
logger.addHandler(file_handler)
logger.setLevel(loglevel)

skipped_translators = []


def insert(txt, translation, lang_code, translators_string, is_translated, is_same):
    con = sqlite3.connect("translations.db")
    cur = con.cursor()
    long_lang = c.LANGUAGES[lang_code]
    src_text = f"\042{txt.replace('$', '_')}\042"
    trans_text = f"\042{translation.replace('$', '_')}\042"
    translators_string = f"\042{translators_string}\042"
    query = f"INSERT OR IGNORE INTO {long_lang} (english, {long_lang}, translators, is_translated, is_same) VALUES({src_text}, {trans_text}, {translators_string}, {is_translated}, {is_same});"
    cur.execute(query)
    con.commit()
    con.close()


def validate_translation(trans_array, original_txt):
    matches = get_close_matches(original_txt, trans_array)
    if len(matches) > 0:
        return matches[0]
    occurence_count = Counter(trans_array)
    counts = sorted(occurence_count.values())
    ct_array = [len(occurence_count.most_common(1)[0][0].split(' ')), len(original_txt.split(' '))]
    ct_array.sort()
    if counts[-1] > 1 and ct_array[1] - ct_array[0] < 2:
        return occurence_count.most_common(1)[0][0]
    if len(trans_array) == 0:
        logger.error(
            f'Could not find a best match for {original_txt} from list: {trans_array}. Using original text.')
        return original_txt
    else:
        return validate_translation(trans_array[:-1], trans_array[0])


def clean(txt):
    s = regex.sub(r'[^a-zA-Z0-9_,\'\.\$\s\p{script=Latin}()-]\'', '', txt).rstrip('.')
    return s


def finalize(txt, token):
    if '_' in txt:
        underscore_loc = txt.rfind('_')
        try:
            if (len(txt) != underscore_loc - 1) and txt[underscore_loc + 1] != ' ':
                txt = txt.replace('_', '_ ')
        except IndexError as e:
            logger.error(f'Retokenization of {txt} with {token} failed: {e}')
    return clean(txt.replace('_', token))


def pronoun(key):
    pronoun_fragments = ['CN']
    for f in pronoun_fragments:
        if f in key:
            return True
    return False


def get_active_pool(lang_code):
    active_pool = copy.copy(c.LANG_TRANS_MAP[lang_code])
    return [t for t in active_pool if t not in skipped_translators]


def translate(key, txt, lang_code):
    logger.info(f'\n[------------------TRANSLATING {txt.upper()} TO {lang_code.upper()}------------------]')
    if txt == '' or txt is None:
        return key, txt
    token = ''
    if '$' in txt:
        try:
            token = regex.search(r'\$\w+\$', txt).group().upper()
        except Exception as e:
            logger.error(f'Token matching failed: {e}')
    txt = regex.sub(r'\$\w+\$', '_', txt).title()
    active_pool = get_active_pool(lang_code)
    translated = check_in_db(txt, lang_code).rstrip('.')
    if translated:
        logger.info(f'Translation({lang_code}) for {txt} found in db: {translated}')
        return key, finalize(translated, token)
    else:
        trans_array = []
        translators = []
        for translator in active_pool:
            logger.debug(f'Current translator pool {active_pool}')
            while len(trans_array) != 5:
                translator = choice(active_pool)
                try:
                    translation = clean(
                        ts.translate_text(txt, translator, from_language='en', to_language=lang_code))
                    trans_array.append(translation)
                    translators.append(translator)
                    logger.info(f'Translator ({translator}) succeeded: {txt} to {translation}')
                except requests.exceptions.SSLError:
                    logger.warning(f'Removing translator {translator} for the pool for this run.')
                    skipped_translators.append(translator)
                except Exception as e:
                    logger.error(
                        f'Translation exception: Text:{txt} | Translator: {translator} | ToLang: {lang_code} | Error: {e}')
                finally:
                    active_pool.remove(translator)
                    if len(active_pool) == 0:
                        active_pool = get_active_pool(lang_code)

            translated = validate_translation(trans_array, txt)
            translators_string = ','.join(translators)
            logger.info(f'Translation of {txt} completed with {translator}: {translated}.')
            insert(txt, translated, lang_code, translators_string, True, True)

        if not translated:
            translated = txt
            insert(txt, translated, lang_code, None, False, True)
        return key, finalize(translated.title(), token)


def _translate(thr_input):
    response = translate(thr_input['key'], thr_input['txt'], thr_input['lang_code'])
    thr_input['queue'].put(response)


def translate_dict(indict, to_lang_code):
    translated_dict = dict()
    counter = 0
    thread_pool = []
    my_queue = Queue()
    thread_inputs = []
    for k, v in indict.items():
        thr_input = {
            "key": k,
            "txt": v,
            "lang_code": to_lang_code,
            "queue": my_queue
        }
        thread_inputs.append(thr_input)

    with ThreadPool(len(indict)) as pool:
        result = pool.map(_translate, thread_inputs)

    while my_queue.qsize() > 0:
        logger.debug(f"Queue length is {my_queue.qsize()}")
        try:
            result = my_queue.get()
            if result != '':
                translated_dict[result[0]] = result[1]
        except Exception as e:
            logger.critical(f'No result from thread! {e}')
    untranslated = [i for i in indict.keys() if i not in translated_dict.keys()]
    for k, v in indict.items():
        if k in untranslated:
            logger.warning(f'Failed to translate {k}: to {v}')
            translated_dict[k] = v

    return translated_dict


def check_in_db(txt, to_lang):
    con = sqlite3.connect("translations.db")
    cur = con.cursor()
    query = f"CREATE TABLE IF NOT EXISTS {c.LANGUAGES[to_lang]} (english varchar, {c.LANGUAGES[to_lang]} varchar, translators varchar, is_translated boolean, is_same boolean, UNIQUE(english))"
    cur.execute(query)
    txt = txt.replace("'", "''")
    lookup = f"SELECT {c.LANGUAGES[to_lang]} FROM {c.LANGUAGES[to_lang]} where english='{txt}'"
    logger.debug(f'Execution query:\n {lookup}')
    res = cur.execute(lookup)
    translation = res.fetchone()
    con.close()
    if translation:
        return translation[0].replace(' •', '')
    else:
        return ''
