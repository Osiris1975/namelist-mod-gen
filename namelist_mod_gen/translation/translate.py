import copy
import datetime
import http
import logging
import multiprocessing.pool as mp
import os
import queue
import sys
import traceback as tb

import deepl
import googletrans
import requests
from easynmt import EasyNMT
from ratelimiter import RateLimiter
from sqlalchemy.exc import IntegrityError

import constants.constants as c
from clean.cleaner import clean_input_text
from db.db import Connection
from token_handlers.handlers import detokenize, retokenize

rate_limiter = RateLimiter(max_calls=c.RL_CALLS, period=c.RL_PERIOD)

db = Connection(db_path=c.DB_PATH, pool_size=c.DB_POOL_SIZE, max_overflow=c.DB_MAX_OVERFLOW,
                pool_timeout=c.DB_POOL_TIMEOUT)

log = logging.getLogger('NMG')

ez_nmt_model = EasyNMT('opus-mt')


class Translator(object):
    def __init__(self, namelist, lang, namelist_id, funcs):
        self.id = namelist_id
        self.namelist_length = len(namelist)
        self.lang = lang
        self.lang_code = c.TABLE_LANGUAGES[lang]
        self.namelist = copy.copy(namelist)
        self.translated = queue.Queue()
        self.untranslated = queue.Queue()
        self.__is_done__ = False
        self.gtrans = googletrans.Translator()
        self.deepl = deepl.Translator(os.getenv('DEEPL_AUTH_KEY'))
        self.lang_table = db.get_language_dict(self.lang)
        self.translated_dict = dict()
        self.usable_funcs = funcs

    def filter_funcs(self):
        usable = []
        all_funcs = {
            self.db_translate: self._do_db_translate,
            self.api_mmt: self._do_mmt,
            self.api_gtrans: self._do_gtrans,
            self.api_deepl: self._do_deepl,
            self.mt_easynmt: self._do_easynmt
        }
        for f1, f2 in all_funcs.items():
            log.info(f'Checking availability of {f1.__name__}')
            not_ok = f"{f1.__name__}'s API endpoint currently not available, removing from translator pool."
            try:
                result = f2(('TEST_KEY', 'hello world'))
                if not result:
                    log.warning(not_ok)
                    continue
                log.info(f"{f1.__name__} available for use.")
                usable.append(f1)
            except Exception as e:
                log.warning(not_ok)
        return usable

    def run(self):
        # self.usable_funcs =
        for loc_key, text in self.namelist.items():
            self.untranslated.put((loc_key, text))
        log.info(f'Available funcs: {",".join([func.__name__ for func in self.usable_funcs])}')
        for func in self.usable_funcs:
            try:
                log.info(f'Beginning translation of {self.id} to {self.lang} with {func.__name__}')
                log.debug(f'Texts requiring translation for lang({self.lang_code}): {self.namelist_length}')
                results = func()
                if self.done():
                    return self.queue_to_dict()
                self.update_queues(results)
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
        if not self.done():
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
        self.__is_done__ = self.translated.qsize() == self.namelist_length and self.untranslated.qsize() == 0
        return self.__is_done__

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
        with mp.ThreadPool() as pool:
            results = pool.map(self._do_db_translate, self.get_remaining())
        return results

    def _do_db_translate(self, loc_kv):
        detokenized = detokenize(loc_kv[1])
        try:
            response = detokenized['translation'] = self.lang_table[detokenized['detokenized_txt']]
        except KeyError:
            log.debug(f'{detokenized["original_txt"]} not found in table for {self.lang}')
            return loc_kv[0], detokenized
        detokenized['translation'] = clean_input_text(response).title()
        return loc_kv[0], detokenized

    def api_gtrans(self):
        log.info(f'Attempting translation with googletrans')
        with mp.ThreadPool() as pool:
            results = pool.map(self._do_gtrans, self.get_remaining())
        return results

    def _do_gtrans(self, loc_kv):
        detokenized = detokenize(loc_kv[1])
        with rate_limiter:
            response = self.gtrans.translate(detokenized['detokenized_txt'], src='en',
                                             dest=self.lang_code.replace('zh', 'zh-CN'))
        detokenized['translation'] = clean_input_text(response.text).title()
        self.translated.put(loc_kv[0], retokenize(detokenized))
        log.debug(
            f'Translation(gtrans:{self.lang_code}) result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
        if detokenized['translation'] not in self.lang_table.values():
            self.insert_one(loc_key=loc_kv[0], detokenized=detokenized, translators='gtrans', translator_mode='api')
        return response

    def api_deepl(self):
        log.info(f'Attempting translation with deepl')
        # try:
        #     with rate_limiter:
        #         self.deepl.translate_text('test', source_lang='en', target_lang=self.lang_code)
        # except deepl.exceptions.QuotaExceededException as e:
        #     log.warning(f'Can not translate using deepl: {e}')
        #     return
        with mp.ThreadPool() as pool:
            results = pool.map(self._do_deepl, self.get_remaining())
        return results

    def to_dl_code(self):
        if self.lang_code in c.DL_CODES.keys():
            return c.DL_CODES[self.lang_code]
        return self.lang_code

    def _do_deepl(self, loc_kv):
        detokenized = detokenize(loc_kv[1])
        with rate_limiter:
            response = self.deepl.translate_text(detokenized['detokenized_txt'], source_lang='en',
                                                 target_lang=self.to_dl_code())
        detokenized['translation'] = clean_input_text(response.text).title()
        self.translated.put(loc_kv[0], retokenize(detokenized))
        log.debug(
            f'Translation(deepl:{self.lang_code}) result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
        if detokenized['translation'] not in self.lang_table.values():
            self.insert_one(loc_key=loc_kv[0], detokenized=detokenized, translators='deepl', translator_mode='api')
        return response

    def api_mmt(self):
        log.info(f'Attempting translation with mmt')
        with mp.ThreadPool() as pool:
            pool.map(self._do_mmt, self.get_remaining())

    def _do_mmt(self, loc_kv):
        detokenized = detokenize(loc_kv[1])
        url = f'https://api.mymemory.translated.net/get?q={detokenized["detokenized_txt"]}&langpair=en|{self.lang_code}'
        # with rate_limiter:
        response = requests.get(url)
        if response.status_code == http.HTTPStatus.TOO_MANY_REQUESTS:
            content = response.json()
            log.warning(f'Daily request quota used up for MMT: {content["responseDetails"]}')
            return
        if response.status_code == http.HTTPStatus.OK:
            detokenized['translation'] = clean_input_text(response.json()['responseData']['translatedText']).title()
            self.insert_one(loc_key=loc_kv[0], detokenized=detokenized, translators='mmt', translator_mode='api')
            self.translated.put(loc_kv[0], retokenize(detokenized))
        log.debug(
            f'Translation(mmt:{self.lang_code}) result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
        return response

    def mt_easynmt(self):
        log.info(f'Attempting translation with googletrans')
        with mp.Pool() as pool:
            results = pool.map(self._do_easynmt, self.get_remaining())
        return results

    def _do_easynmt(self, loc_kv):
        detokenized = detokenize(loc_kv[1])
        response = ez_nmt_model.translate(detokenized['detokenized_txt'], source_lang='en', target_lang=self.lang_code)
        detokenized['translation'] = clean_input_text(response).title()
        self.insert_one(loc_key=loc_kv[0], detokenized=detokenized, translators='easynmt', translator_mode='api')
        log.debug(
            f'Translation(easynmt:{self.lang_code}) result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
        return response
