import copy
import datetime
import logging
import os
import re
import sqlite3
import threading
from collections import Counter
from difflib import get_close_matches
from queue import Queue
from random import shuffle, choice

import colorlog
import translators as ts

from src.namelist_mod_gen.constants import constants as c

exitFlag = 0
loglevel = os.getenv('LOG_LEVEL').upper()
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s[%(asctime)s][%(levelname)s][%(name)s]: %(message)s'))
file_handler = logging.FileHandler(filename=f"{c.PROJECT_DIR}/logs/{datetime.datetime.now().strftime('%d.%m.%Y_%H.%M.%S')}.translation.log")
file_handler.setFormatter(logging.Formatter('[%(asctime)s][%(levelname)s][%(name)s]: %(message)s'))
file_handler.setLevel(loglevel)

logger = colorlog.getLogger('__main__.' + __name__)
logger.addHandler(handler)
logger.addHandler(file_handler)
logger.setLevel(loglevel)

threadLimiter = threading.BoundedSemaphore(100)


class TransThread(threading.Thread):
    def __init__(self, threadID, name, key, word, to_lang_code, queue):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.word = word
        self.key = key
        self.to_lang_code = to_lang_code
        self.queue = queue

    def run(self):
        threadLimiter.acquire()
        try:
            translate_response = translate(self.key, self.word, self.to_lang_code)
            self.queue.put(translate_response)
        finally:
            threadLimiter.release()



def insert(txt, translation, lang_code):
    con = sqlite3.connect("translations.db")
    cur = con.cursor()
    long_lang = c.LANGUAGES[lang_code]
    src_text = f"\042{txt.replace('$', '_')}\042"
    trans_text = f"\042{translation.replace('$', '_')}\042"
    query = f"INSERT OR IGNORE INTO {long_lang} (english, {long_lang}) VALUES({src_text}, {trans_text});"
    cur.execute(query)
    con.commit()
    con.close()


def validate_translation(trans_array, original_txt):
    matches = get_close_matches(original_txt, trans_array)
    if len(matches) > 0:
        return matches[0].replace(' •', '')
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


def finalize(txt, token):
    underscore_loc = txt.rfind('_')
    if (len(txt) != underscore_loc - 1) and txt[underscore_loc + 1] != ' ':
        txt = txt.replace('_', '_ ')
    return txt.replace('_', token).rstrip('.').replace(' •', '')


def translate(key, txt, to_lang):
    logger.info(f'\n[------------------TRANSLATING {txt.upper()} TO {to_lang.upper()}------------------]')
    if txt == '' or txt is None:
        return key, txt
    token = ''
    if '$' in txt:
        token = re.match(r'\$\S+\$', txt).group().upper()
        txt = txt.replace(token, '_')
    active_pool = copy.copy(c.LANG_TRANS_MAP[to_lang])
    translated = check_in_db(txt, to_lang).rstrip('.')
    if translated:
        logger.info(f'Translation({to_lang}) for {txt} found in db: {translated}')
        return key, finalize(translated, token)
    else:
        for translator in active_pool:
            if translator in ['utiibet', 'lingvanex']:
                from_lang = 'en_GB'
            else:
                from_lang = 'en'
            logger.debug(f'Current translator pool {active_pool}')
            try:
                trans_array = [ts.translate_text(txt, translator, from_language=from_lang, to_language=to_lang)]
                for i in range(0, 2):
                    trans_array.append(ts.translate_text(txt, choice(active_pool),
                                                         from_language='en',
                                                         to_language=to_lang).replace(' •', ''))
                translated = validate_translation(trans_array, txt).rstrip('.')
                logger.info(f'Translation of {txt} completed with {translator}: {translated}.')
                insert(txt, translated, to_lang)
                break

            except Exception as e:
                logger.error(f'Translation exception: Text:{txt} Translator: {translator} | ToLang: {to_lang} | Error: {e}')
                active_pool.remove(translator)

                if len(active_pool) > 2:
                    logger.debug(
                        f'Translation of {txt} failed using {translator} with {e} Trying another one from list: {active_pool}')
                else:
                    logger.warning(f'Ran out of translator options. Resetting the translator pool.')
                    active_pool = copy.copy(c.LANG_TRANS_MAP[to_lang])
            finally:
                shuffle(active_pool)

        if not translated:
            translated = txt
            insert(txt, translated, to_lang)
        return key, finalize(translated, token)


def translate_dict(indict, to_lang_code):
    translated_dict = dict()
    counter = 0
    thread_pool = []
    my_queue = Queue()
    for k, v in indict.items():
        this_cnt = counter + 1
        thread_id = f'{k}_{v}'
        logger.debug(f'Attempting to translate {k}: {v} to {to_lang_code}')
        thread = TransThread(this_cnt, thread_id, k, v, to_lang_code, my_queue)
        thread_pool.append(thread)

    for thread in thread_pool:
        thread.start()

    for thread in thread_pool:
        thread.join()

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
    query = f"CREATE TABLE IF NOT EXISTS {c.LANGUAGES[to_lang]} (english varchar, {c.LANGUAGES[to_lang]} varchar, UNIQUE(english))"
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
