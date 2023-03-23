import copy
import datetime
import http
import logging
import os
import sqlite3
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
from src.namelist_mod_gen.validation.validation import validate_translation, validate

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


def update(txt, translation, lang_code, translators_string, mode, namelist_category, writer, begin=True):
    try:
        cur = writer.cursor()
        long_lang = c.LANGUAGES[lang_code]
        src_text = f"\042{txt}\042"
        trans_text = f"\042{translation}\042"
        translators_string = f"\042{translators_string}\042"
        mode = f"\042{mode}\042"
        cat = f"\042{namelist_category}\042"
        query = f"UPDATE {long_lang} set translation = {trans_text}, translators = {translators_string}, translator_mode = {mode}, namelist_category = {cat}, translation_date = CURRENT_TIMESTAMP where english = {src_text};"
        logger.debug(f'Insert Query: {query}')
        if begin:
            cur.execute("BEGIN")
        cur.execute(query)
        writer.commit()
        logger.info(
            f'\n[------------------{translation.upper()} INSERTED INTO DB FOR {lang_code.upper()}------------------]')
    except Exception as e:
        logger.error(f'Failed to insert {txt}:{translation} into DB: {e}')


def insert(txt, translation, lang_code, translators_string, mode, namelist_category, writer, begin=True):
    try:
        cur = writer.cursor()
        long_lang = c.LANGUAGES[lang_code]
        src_text = f"\042{txt}\042"
        trans_text = f"\042{translation}\042"
        translators_string = f"\042{translators_string}\042"
        mode = f"\042{mode}\042"
        cat = f"\042{namelist_category}\042"
        query = f"INSERT OR IGNORE INTO {long_lang} (english, translation, translators, translator_mode, namelist_category, translation_date) VALUES({src_text}, {trans_text}, {translators_string}, {mode}, {cat}, CURRENT_TIMESTAMP);"
        logger.debug(f'Insert Query: {query}')
        if begin:
            cur.execute("BEGIN")
        cur.execute(query)
        writer.commit()
        logger.info(
            f'\n[------------------{translation.upper()} INSERTED INTO DB FOR {lang_code.upper()}------------------]')
    except Exception as e:
        logger.error(f'Failed to insert {txt}:{translation} into DB: {e}')


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


def random_api_translation(txt, lang_code, writer, begin):
    translation = None
    active_pool = get_active_pool(lang_code)
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
        insert(txt, translation.title(), lang_code, translators_string, 'api', None, writer, begin)

    return translation


def mymemory_translation(txt, lang_code, writer, begin):
    url = f'https://api.mymemory.translated.net/get?q={txt}&langpair=en|{lang_code}'
    response = requests.get(url)
    if response.status_code == http.HTTPStatus.OK:
        translation = response.json()['responseData']['translatedText']
        if writer:
            insert(txt, translation.title(), lang_code, 'mmt', 'machine', None, writer, begin)
        return translation
    else:
        skipped_methods.append('mmt')


def deepl_translation(txt, lang_code, writer, begin):
    try:
        translation = dl_translator.translate_text(txt, target_lang=to_dl_code(lang_code),
                                                   preserve_formatting=True).text
        insert(txt, translation.title(), lang_code, 'deepl', 'machine', None, writer, begin)
        return translation
    except Exception as e:
        logger.error(f'Translation with deepl failed: {e}')
        skipped_methods.append('deepl')


def easy_nmt_translation(txt, lang_code, writer, begin):
    try:
        translation = ez_nmt_model.translate(txt, source_lang='en', target_lang=lang_code)
        insert(txt, translation.title(), lang_code, 'easy_nmt', 'machine', None, writer, begin)
        return translation

    except requests.exceptions.HTTPError as e:
        logger.error(f'Translation with easy-nmt failed: {e}')


def gtrans_translation(txt, lang_code, writer, begin):
    try:
        translation = g_trans.translate(txt, src='en', dest=lang_code).text
        insert(txt, translation.title(), lang_code, 'gtrans', 'api', None, writer, begin)
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


def translate(key, txt, lang_code, writer, reader, begin):
    if txt == '' or txt is None:
        return key, txt
    logger.info(f'\n[------------------PROCESSING {txt.upper()} TO {lang_code.upper()}------------------]')
    txt = pre_clean(txt)
    txt_dict = resolve_token_placement(txt)
    # check local DB first
    txt = txt_dict['detokenized_txt']
    tr_method = None
    translated = None
    if not translated and 'gtrans' not in skipped_methods:
        logger.debug(
            f'\n[------------------TRANSLATING WITH GTRANS MODE: {txt.upper()} TO {lang_code.upper()}------------------]')
        translated = gtrans_translation(txt_dict['detokenized_txt'], lang_code, writer, begin)
        tr_method = 'gtrans'

    if not translated and 'mmt' not in skipped_methods:
        logger.debug(
            f'\n[------------------TRANSLATING WITH MMT MODE: {txt.upper()} TO {lang_code.upper()}------------------]')
        translated = mymemory_translation(txt_dict['detokenized_txt'], lang_code, writer, begin)
        tr_method = 'mmt'

    if not translated and 'deepl' not in skipped_methods:
        deepl_lang_code = to_dl_code(lang_code)
        logger.debug(
            f'\n[------------------TRANSLATING WITH DEEPL MODE: {txt.upper()} TO {lang_code.upper()}------------------]')
        translated = deepl_translation(txt_dict['detokenized_txt'], deepl_lang_code, writer, begin)
        tr_method = 'deepl'

    if not translated and lang_code not in c.OPUS_UNSUPPORTED:
        logger.debug(
            f'\n[------------------TRANSLATING WITH EASY-NMT MODE: {txt.upper()} TO {lang_code.upper()}------------------]')
        translated = easy_nmt_translation(txt_dict['detokenized_txt'], lang_code, writer, begin)
        tr_method = 'easy-nmt'

    if not translated:
        logger.debug(
            f'\n[------------------TRANSLATING WITH RANDOM API MODE: {txt.upper()} TO {lang_code.upper()}------------------]')
        translated = random_api_translation(txt_dict['detokenized_txt'], lang_code, writer, begin)
        tr_method = 'random-api'

    if not translated:
        logger.warning(
            f'All translation methods failed to translate {txt_dict["detokenized_txt"]} to {lang_code}'
        )
        translated = txt_dict['detokenized_txt']

    if len(validate(translated)) > 0:
        logger.warning(f'{translated} is a namelist incompatible translation({tr_method}). Using original value.')
        translated = txt

    retokenized = retokenize(translated.title(), txt_dict)
    cleaned = clean(retokenized)
    logger.info(
        f'Translation succeeded | Original: {txt} | Translation: {cleaned} | ToLang: {lang_code} | TrMethod: {tr_method}')
    return key, cleaned


def _translate(thr_input):
    reader = sqlite3.connect('translations.db', timeout=15, isolation_level=None)
    writer = sqlite3.connect('translations.db', timeout=15, isolation_level=None)
    try:
        reader.execute('pragma journal_mode=wal;')
        writer.execute('pragma journal_mode=wal;')
        response = translate(thr_input['key'], thr_input['txt'], thr_input['lang_code'], writer, reader, True)
        thr_input['queue'].put(response)
    except Exception as e:
        logger.error(f'Translation thread failure: {e}')
    finally:
        # reader.close()
        # writer.close()
        pass


def translate_dict(indict, to_lang_code, translate):
    if translate:
        table_reader = sqlite3.connect('translations.db', timeout=15, isolation_level=None)
        table_reader.row_factory = sqlite3.Row
        cur = table_reader.cursor()
        cur.execute(f'select * from {c.LANGUAGES[to_lang_code]}')
        result = cur.fetchall()
        lang_dict = {dict(r)['english']: dict(r) for r in result}

        translated_dict = dict()

        my_queue = Queue()
        thread_inputs = []
        for k, v in indict.items():
            if v in lang_dict.keys():
                translated_dict[k] = v
            else:
                thr_input = {
                    "key": k,
                    "txt": v,
                    "lang_code": to_lang_code,
                    "queue": my_queue,
                    "lang_dict": lang_dict
                }
                thread_inputs.append(thr_input)
        with ThreadPool() as pool:
            pool.map(_translate, thread_inputs)

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


try:
    dl_translator = deepl.Translator(os.getenv('DEEPL_AUTH_KEY'))
    dl_translator.translate_text('test', target_lang='es')
    dl_langs = dl_translator.get_target_languages()
except Exception as e:
    skipped_methods.append('deepl')

try:
    mymemory_translation(txt='test', lang_code='es', writer=None)
except Exception as e:
    skipped_methods.append('mmt')
