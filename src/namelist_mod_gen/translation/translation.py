import copy
import datetime
import http
import logging
import os
import random
import sqlite3
import time
from collections import Counter
from difflib import get_close_matches
from multiprocessing.pool import ThreadPool
from queue import Queue
from random import choice

import colorlog
import deepl
import googletrans
import regex
import requests.exceptions
import translators as ts
from easynmt import EasyNMT

from src.namelist_mod_gen.constants import constants as c

try:
    loglevel = os.getenv('LOG_LEVEL').upper()
except AttributeError:
    loglevel = 'INFO'

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
skipped_methods = []
g_trans = googletrans.Translator()

ez_nmt_model = EasyNMT('opus-mt')


def insert(txt, translation, lang_code, translators_string, is_translated, is_same, writer):
    try:
        cur = writer.cursor()
        long_lang = c.LANGUAGES[lang_code]
        src_text = f"\042{txt}\042"
        trans_text = f"\042{translation}\042"
        translators_string = f"\042{translators_string}\042"
        query = f"INSERT OR IGNORE INTO {long_lang} (english, {long_lang}, translators, is_translated, is_same) VALUES({src_text}, {trans_text}, {translators_string}, {is_translated}, {is_same});"
        logger.debug(f'Insert Query: {query}')
        cur.execute("BEGIN")
        cur.execute(query)
        writer.commit()
        writer.close()
        logger.info(
            f'\n[------------------{translation.upper()} INSERTED INTO DB FOR {lang_code.upper()}------------------]')
    except Exception as e:
        logger.error(f'Failed to insert {txt}:{translation} into DB: {e}')


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
    try:
        s = regex.sub(r'[^a-zA-Z0-9_,\'\.\$\s\p{script=Latin}()-]\'', '', txt).rstrip('.')
        s = s.replace("'S", "'s")
        return s
    except Exception as e:
        logger.error(f'Error cleaning text: {txt}: {e}')


def retokenize(translation, txt_dict):
    if txt_dict['loc'] == 1:
        return f'{txt_dict["token"]} {translation}'
    if txt_dict['loc'] == 2:
        return f'{translation} {txt_dict["token"]}'
    return translation


def get_active_pool(lang_code):
    active_pool = copy.copy(c.LANG_TRANS_MAP[lang_code])
    return [t for t in active_pool if t not in skipped_translators]


def rand_wait():
    time.sleep(random.randint(0, 10))


def random_api_translation(txt, lang_code, writer):
    translation = None
    active_pool = get_active_pool(lang_code)
    trans_array = []
    translators = []
    for translator in active_pool:
        logger.debug(f'Current translator pool {active_pool}')
        while len(trans_array) != 5:
            rand_wait()
            translator = choice(active_pool)
            try:
                translation = clean(
                    ts.translate_text(txt, translator, from_language='en', to_language=lang_code))
                trans_array.append(translation)
                translators.append(translator)
            except requests.exceptions.SSLError:
                logger.warning(f'Removing translator {translator} for the pool for this run.')
                skipped_translators.append(translator)
            except Exception as e:
                logger.error(
                    f'Random API Mode Translation Failed | Original: {txt} | ToLang: {lang_code} | Translator: {translator} | Exception: {e}')
            finally:
                active_pool.remove(translator)
                if len(active_pool) == 0:
                    active_pool = get_active_pool(lang_code)

        translation = validate_translation(trans_array, txt)
        translators_string = ','.join(translators)
        logger.info(f'Translation of {txt} to {lang_code} completed with {translator}: {translation}.')
        insert(txt, translation.title(), lang_code, translators_string, True, True, writer)

    return translation


def mymemory_translation(txt, lang_code, writer):
    url = f'https://api.mymemory.translated.net/get?q={txt}&langpair=en|{lang_code}'
    response = requests.get(url)
    if response.status_code == http.HTTPStatus.OK:
        translation = response.json()['responseData']['translatedText']
        insert(txt, translation.title(), lang_code, 'mmt', True, True, writer)
        return translation
    else:
        skipped_methods.append('mmt')


def deepl_translation(txt, lang_code, writer):
    try:
        translation = dl_translator.translate_text(txt, target_lang=to_dl_code(lang_code),
                                                   preserve_formatting=True).text
        insert(txt, translation.title(), lang_code, 'deepl', True, True, writer)
        return translation
    except Exception as e:
        logger.error(f'Translation with deepl failed: {e}')
        skipped_methods.append('deepl')


def easy_nmt_translation(txt, lang_code, writer):
    try:
        translation = ez_nmt_model.translate(txt, source_lang='en', target_lang=lang_code)
        insert(txt, translation.title(), lang_code, 'easy_nmt', True, True, writer)
        return translation

    except requests.exceptions.HTTPError as e:
        logger.error(f'Translation with easy-nmt failed: {e}')


def gtrans_translation(txt, lang_code, writer):
    try:
        translation = g_trans.translate(txt, src='en', dest=lang_code).text
        insert(txt, translation.title(), lang_code, 'gtrans', True, True, writer)
        return translation
    except Exception as e:
        logger.error(f'Translation with gtrans failed: {e}')
        skipped_methods.append('gtrans')


def resolve_token_placement(txt):
    try:
        detokenized_txt = regex.sub(r'\$\w+\$', '', txt)
        response = {
            'original_txt': txt,
            'detokenized_txt': detokenized_txt.title().strip(),
            'token': '',
            'loc': 0
        }
        token = regex.search(r'^\$\w+\$', txt)
        if token:
            response['token'] = token.group()
            response['loc'] = 1
        token = regex.search(r'\$\w+\$$', txt)
        if token:
            response['token'] = token.group()
            response['loc'] = 2
        token = regex.search(r'\(\w+\)', txt)
        if token:
            response['token'] = token.group()
            response['detokenized_txt'] = txt.replace(response['token'], '').title()
            response['loc'] = 2
        return response
    except Exception as e:
        logger.error(f'Token matching failed: {e}')


def pre_clean(txt):
    return txt.strip()


def to_dl_code(lang_code):
    if lang_code in c.DL_CODES.keys():
        return c.DL_CODES[lang_code]
    return lang_code


def translate(key, txt, lang_code, writer, reader):
    if txt == '' or txt is None:
        return key, txt
    logger.info(f'\n[------------------PROCESSING {txt.upper()} TO {lang_code.upper()}------------------]')
    txt = pre_clean(txt)
    txt_dict = resolve_token_placement(txt)
    # check local DB first
    txt = txt_dict['detokenized_txt']
    tr_method = None
    translated = check_in_db(txt_dict['detokenized_txt'], lang_code, reader)
    if translated:
        tr_method = 'db'
        logger.debug(f'\n[------------------ {txt.upper()} FOUND IN DB ------------------]')

    if not translated and 'gtrans' not in skipped_methods:
        logger.debug(
            f'\n[------------------TRANSLATING WITH GTRANS MODE: {txt.upper()} TO {lang_code.upper()}------------------]')
        translated = gtrans_translation(txt_dict['detokenized_txt'], lang_code, writer)
        tr_method = 'gtrans'

    if not translated and 'mmt' not in skipped_methods:
        logger.debug(
            f'\n[------------------TRANSLATING WITH MMT MODE: {txt.upper()} TO {lang_code.upper()}------------------]')
        translated = mymemory_translation(txt_dict['detokenized_txt'], lang_code, writer)
        tr_method = 'mmt'

    if not translated and 'deepl' not in skipped_methods:
        deepl_lang_code = to_dl_code(lang_code)
        logger.debug(
            f'\n[------------------TRANSLATING WITH DEEPL MODE: {txt.upper()} TO {lang_code.upper()}------------------]')
        translated = deepl_translation(txt_dict['detokenized_txt'], deepl_lang_code, writer)
        tr_method = 'deepl'

    if not translated and lang_code not in c.OPUS_UNSUPPORTED:
        logger.debug(
            f'\n[------------------TRANSLATING WITH EASY-NMT MODE: {txt.upper()} TO {lang_code.upper()}------------------]')
        translated = easy_nmt_translation(txt_dict['detokenized_txt'], lang_code, writer)
        tr_method = 'easy-nmt'

    if not translated:
        logger.debug(
            f'\n[------------------TRANSLATING WITH RANDOM API MODE: {txt.upper()} TO {lang_code.upper()}------------------]')
        translated = random_api_translation(txt_dict['detokenized_txt'], lang_code, writer)
        tr_method = 'random-api'

    if not translated:
        logger.warning(
            f'All translation methods failed to translate {txt_dict["detokenized_txt"]} to {lang_code}'
        )
        translated = txt_dict['detokenized_txt']
    retokenized = retokenize(translated.title(), txt_dict)
    cleaned = clean(retokenized)
    logger.info(
        f'Translation succeeded | Original: {txt} | Translation: {cleaned} | ToLang: {lang_code} | TrMethod: {tr_method}')
    return key, cleaned


def _translate(thr_input):
    rand_wait()
    reader = sqlite3.connect('translations.db', timeout=15, isolation_level=None)
    writer = sqlite3.connect('translations.db', timeout=15, isolation_level=None)
    try:
        reader.execute('pragma journal_mode=wal;')
        writer.execute('pragma journal_mode=wal;')
        response = translate(thr_input['key'], thr_input['txt'], thr_input['lang_code'], writer, reader)
        thr_input['queue'].put(response)
    except Exception as e:
        logger.error(f'Translation thread failure: {e}')
    finally:
        reader.close()
        writer.close()


def translate_dict(indict, to_lang_code, translate):
    if translate:
        translated_dict = dict()
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
        # TODO: Need to handle issue where sometimes waiter.acquire never acquires
        with ThreadPool(c.THREAD_CONCURRENCY) as pool:
            results = pool.map(_translate, thread_inputs, chunksize=10)

        for r in results:
            print(r)

        while my_queue.qsize() > 0:
            logger.debug(f"Queue length is {my_queue.qsize()}")
            try:
                result = my_queue.get()
                if result != '':
                    translated_dict[result[0]] = result[1]
            except Exception as e:
                logger.critical(f'No result from thread! {e}')

        untranslated = [i for i in indict.keys() if i not in translated_dict.keys()]
        for e in untranslated:
            translated_dict[e] = indict[e]

        return translated_dict
    else:
        return indict


def check_in_db(txt, to_lang, reader):
    cur = reader.cursor()
    txt = txt.replace("'", "''")
    lookup = f"SELECT {c.LANGUAGES[to_lang]} FROM {c.LANGUAGES[to_lang]} where english='{txt}'"
    logger.debug(f'Execution query:\n {lookup}')
    cur.execute('BEGIN')
    res = cur.execute(lookup)
    translation = res.fetchone()
    if translation:
        return translation[0].replace(' •', '')
    else:
        return ''


try:
    dl_translator = deepl.Translator(os.getenv('DEEPL_AUTH_KEY'))
    deepl_translation('test', 'es')
    dl_langs = dl_translator.get_target_languages()
except Exception as e:
    skipped_methods.append('deepl')

try:
    mymemory_translation('test', lang_code='es')
except Exception as e:
    skipped_methods.append('mmt')
