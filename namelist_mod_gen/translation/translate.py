import copy
import datetime
import http
import logging
import multiprocessing as mp
import os
import sys
import traceback as tb
import warnings
from concurrent.futures import ThreadPoolExecutor

import deepl
import googletrans
import requests
from easynmt import EasyNMT
from sqlalchemy.exc import IntegrityError

import constants.constants as c
from clean.cleaner import clean_input_text
from db.db import Connection
from token_handlers.handlers import detokenize, retokenize

warnings.simplefilter(action='ignore', category=UserWarning)

db = Connection(db_path=c.DB_PATH, pool_size=c.DB_POOL_SIZE, max_overflow=c.DB_MAX_OVERFLOW,
                pool_timeout=c.DB_POOL_TIMEOUT)

log = logging.getLogger('NMG')


class Translator(object):
    def __init__(self, namelist, lang, namelist_id, available_apis):
        self.id = namelist_id
        self.namelist_length = len(namelist)
        # TODO: Need to get usable_funcs populated properly
        available_funcs = [self.db_translate]
        available_funcs.extend([getattr(self, name) for name in available_apis])
        available_funcs.append(self.mt_easynmt)
        self.usable_funcs = available_funcs
        self.lang = lang
        self.lang_code = c.TABLE_LANGUAGES[lang]
        self.namelist = copy.copy(namelist)
        m = mp.Manager()
        self.translated = m.Queue()
        self.untranslated = m.Queue()
        self.is_done = False
        self.gtrans = googletrans.Translator()
        self.deepl = deepl.Translator(os.getenv('DEEPL_AUTH_KEY'))
        self.lang_table = db.get_language_dict(self.lang)
        self.translated_dict = dict()

    def run(self):
        # seed untranslated queue with all namelist loc_key, text pairs
        for loc_key, text in self.namelist.items():
            self.untranslated.put((loc_key, text))

        # iterate over usable functions and peform cascading translation
        results = None
        for func in self.usable_funcs:
            try:
                log.info(f'Beginning translation of {self.id} to {self.lang} with {func.__name__}')
                log.debug(f'Texts requiring translation for lang({self.lang_code}): {self.namelist_length}')
                results = func()
                self.update_queues(results)
                if len(results) == self.namelist_length:
                    log.info(
                        f'Translation complete! ID:{self.id} | Lang: {self.lang_code} | Translated texts: {self.namelist_length}')
                    return self.queue_to_dict()
                log.info(
                    f'{func.__name__} for {self.id} partially completed: Translated: {self.translated.qsize()} | Remaining {self.untranslated.qsize()}')
            except IntegrityError as e:
                if 'UniqueViolation' in str(e):
                    log.warning(f'Translated text already exists: {e}')
                    log.debug(tb.format_exc())
                else:
                    log.error(f'Unexpected database error: {e}')
            except Exception as e:
                log.error(f'Unexpected error occurred: {e}')
                log.error(tb.format_exc())
                continue
        if len(results) != self.namelist_length:
            log.error(
                f'Translation methods exhausted with {self.translated.qsize()} translations remaining. Exiting...')
            sys.exit(1)

    def queue_to_dict(self):
        while self.translated.qsize() > 0:
            log.debug(f"Queue length is {self.translated.qsize()}")
            try:
                result = self.translated.get()
                self.translated_dict[result[0]] = result[1]
            except Exception as e:
                log.critical(f'Problem processing translation queue: {e}')
        log.debug(f'Finished processing translation queue: {self.translated.qsize()} ')
        return self.translated

    def get_remaining(self):
        inputs = []
        while self.untranslated.qsize() > 0:
            inputs.append(self.untranslated.get())
        return inputs

    def update_queues(self, results):
        log.debug(
            f'Update Queues Begin: Translated length: {self.translated.qsize()} | Untranslated length: {self.untranslated.qsize()}')
        for loc_key, tl_dict in results:
            if tl_dict.get('translation'):
                self.translated.put((loc_key, retokenize(tl_dict)))
            else:
                self.untranslated.put((loc_key, tl_dict['original_txt']))

        log.debug(
            f'Update Queues End: Translated length: {self.translated.qsize()} | Untranslated length: {self.untranslated.qsize()}')

    def done(self):
        tq_size = self.translated.qsize()
        uq_size = self.untranslated.qsize()
        sum_qsize = tq_size + uq_size
        eq_nl_size = sum_qsize == self.namelist_length
        log.info(
            f'Done Check:{eq_nl_size}: TQ Size({tq_size}) + UQ Size({uq_size}) = {sum_qsize}: NL Size: {self.namelist_length}')
        self.is_done = self.translated.qsize() == self.namelist_length and self.untranslated.qsize() == 0
        return self.is_done

    # TODO: If chunked translations is implemented this may be useful.
    # def insert_many(self, objects, translators, translator_mode, language, date):
    #     db.add_many(objects, translators, translator_mode, language, date)

    def insert_one(self, loc_key, detokenized, translators, translator_mode):
        category = None
        for k, v in c.NAMELIST_CATEGORY_TAGS.items():
            if k in loc_key:
                category = v
        db.add_row(
            localisation_key=loc_key,
            language=self.lang,
            english=detokenized['detokenized_txt'],
            translation=detokenized['translation'],
            translators=translators,
            translator_mode=translator_mode,
            namelist_category=category,
            translation_date=datetime.datetime.now()
        )

    def db_translate(self):
        log.info(f'Getting {self.lang} translations from database')
        with ThreadPoolExecutor(max_workers=c.MAX_WORKERS) as executor:
            results = list(executor.map(self._do_db_translate, self.get_remaining()))
        return results

    def _do_db_translate(self, loc_kv):
        detokenized = detokenize(loc_kv[1])
        try:
            response = detokenized['translation'] = self.lang_table[detokenized['detokenized_txt']]
            detokenized['translation'] = clean_input_text(response).title()
            self.translated.put(loc_kv[0], retokenize(detokenized))
        except KeyError:
            log.debug(f'{detokenized["original_txt"]} not found in table for {self.lang}')
            self.untranslated.put(loc_kv)
        detokenized['translation'] = clean_input_text(response).title()
        return loc_kv[0], detokenized

    def api_gtrans(self):
        log.info(f'Attempting translation with googletrans')
        with ThreadPoolExecutor(max_workers=c.MAX_WORKERS) as executor:
            results = list(executor.map(self._do_gtrans, self.get_remaining()))
        return results

    def _do_gtrans(self, loc_kv):
        detokenized = detokenize(loc_kv[1])
        response = self.gtrans.translate(detokenized['detokenized_txt'], src='en',
                                         dest=self.lang_code.replace('zh', 'zh-CN'))
        detokenized['translation'] = clean_input_text(response.text).title()
        self.translated.put(loc_kv[0], retokenize(detokenized))
        log.debug(
            f'Translation(gtrans:{self.lang_code}) result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
        if detokenized['translation'] not in self.lang_table.values() and loc_kv[0] != 'TEST_KEY':
            self.insert_one(loc_key=loc_kv[0], detokenized=detokenized, translators='gtrans', translator_mode='api')
        return loc_kv[0], detokenized

    def api_deepl(self):
        log.info(f'Attempting translation with deepl')
        with ThreadPoolExecutor(max_workers=c.MAX_WORKERS) as executor:
            results = list(executor.map(self._do_deepl, self.get_remaining()))
        return results

    def to_dl_code(self):
        if self.lang_code in c.DL_CODES.keys():
            return c.DL_CODES[self.lang_code]
        return self.lang_code

    def _do_deepl(self, loc_kv):
        detokenized = detokenize(loc_kv[1])
        response = self.deepl.translate_text(detokenized['detokenized_txt'], source_lang='en',
                                             target_lang=self.to_dl_code())
        detokenized['translation'] = clean_input_text(response.text).title()
        self.translated.put(loc_kv[0], retokenize(detokenized))
        log.debug(
            f'Translation(deepl:{self.lang_code}) result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
        if detokenized['translation'] not in self.lang_table.values() and loc_kv[0] != 'TEST_KEY':
            self.insert_one(loc_key=loc_kv[0], detokenized=detokenized, translators='deepl', translator_mode='api')
        return loc_kv[0], detokenized

    def api_mmt(self):
        log.info(f'Attempting translation with mmt')
        with ThreadPoolExecutor(max_workers=c.MAX_WORKERS) as executor:
            results = list(executor.map(self._do_mmt, self.get_remaining()))
        return results

    def _do_mmt(self, loc_kv):
        detokenized = detokenize(loc_kv[1])
        url = f'https://api.mymemory.translated.net/get?q={detokenized["detokenized_txt"]}&langpair=en|{self.lang_code}'
        response = requests.get(url)
        if response.status_code == http.HTTPStatus.TOO_MANY_REQUESTS:
            content = response.json()
            log.warning(f'Daily request quota used up for MMT: {content["responseDetails"]}')
            return
        if response.status_code == http.HTTPStatus.OK and loc_kv[0] != 'TEST_KEY':
            detokenized['translation'] = clean_input_text(response.json()['responseData']['translatedText']).title()
            self.insert_one(loc_key=loc_kv[0], detokenized=detokenized, translators='mmt', translator_mode='api')
            self.translated.put(loc_kv[0], retokenize(detokenized))
        log.debug(
            f'Translation(mmt:{self.lang_code}) result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
        return loc_kv[0], detokenized

    def mt_easynmt(self):
        keys = []
        vals = []
        remaining = self.get_remaining()
        keys = [i[0] for i in remaining]
        detokenized = [detokenize(i[1]) for i in remaining]
        for_translation = [i['detokenized_txt'] for i in detokenized]
        easynmt = EasyNMT(c.OPUS_MODELS[self.lang])
        log.info(f'Remaining {len(for_translation)} untranslated items for {self.id} will be translated with easynmt')
        response = easynmt.translate(for_translation, source_lang='en', target_lang=self.lang_code)
        print()
        # try:
        #     response = easynmt.translate(detokenized['detokenized_txt'], source_lang='en',
        #                                  target_lang=lang_code)
        # except Exception as e:
        #     log.error(f'Problem using easnmt translation: {e}')
        #     return loc_kv[0], detokenized

        # results = list(executor.map(_do_easynmt_wrapper,
        #                             [(self.lang, self.lang_code, loc_kv) for loc_kv in self.get_remaining()]))
        return


#
# def _do_easynmt_wrapper(args):
#     lang, lang_code, loc_kv = args
#     easynmt = EasyNMT(c.OPUS_MODELS[lang])
#     detokenized = detokenize(loc_kv[1])
#
#     try:
#         response = easynmt.translate(detokenized['detokenized_txt'], source_lang='en',
#                                      target_lang=lang_code)
#     except Exception as e:
#         log.error(f'Problem using easnmt translation: {e}')
#         return loc_kv[0], detokenized
#
#     detokenized['translation'] = clean_input_text(response).title()
#     log.debug(
#         f'Translation(easynmt:{lang_code}) result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
#     return loc_kv[0], detokenized


def check_api_availability():
    available = []
    test_phrase = 'hello_world'
    test_lang = 'es'

    gtrans_response = googletrans.Translator().translate(text=test_phrase, dest=test_lang)
    if gtrans_response:
        available.append('api_gtrans')
        log.info(f'Google API available for use')
    else:
        log.warning(f'Google API not available for use in this run so we won\'t use it')
    url = f'https://api.mymemory.translated.net/get?q={test_phrase}&langpair=en|{test_lang}'
    mmt_response = requests.get(url)
    if mmt_response.status_code == http.HTTPStatus.OK:
        available.append('api_mmt')
        log.info(f'MyMemory API available for use')
    else:
        log.warning(f'MyMemory API not available for use in this run so we won\'t use it')
    dl = deepl.Translator(os.getenv('DEEPL_AUTH_KEY'))
    try:
        dl.translate_text(test_phrase, source_lang='en', target_lang=test_lang)
        available.append('api_deepl')
        log.info(f'Deepl API available for use')
    except Exception as e:
        log.warning(f'Deepl API not available for use in this run so we won\'t use it ({e})')
    return available
