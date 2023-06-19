import datetime
import http
import logging
import os
import traceback as tb
import warnings
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Lock

import deepl
import googletrans
import httpcore
import requests
from easynmt import EasyNMT
from ratelimit import limits, sleep_and_retry
from sqlalchemy.exc import IntegrityError
from google.cloud import translate_v2 as gtranslate

import constants.constants as c
from clean.cleaner import clean_input_text
from db.db import Connection
from token_handlers.handlers import detokenize, retokenize

warnings.simplefilter(action='ignore', category=UserWarning)

db = Connection(db_path=c.DB_PATH, pool_size=c.DB_POOL_SIZE, max_overflow=c.DB_MAX_OVERFLOW,
                pool_timeout=c.DB_POOL_TIMEOUT)

log = logging.getLogger('NMG')

skipped_translators = set()


class Translator(object):
    """
    A class that iterates over a series of translation functions to generate translations from a dictionaru of keys
    whose values are to be translated.
    """

    def __init__(self, **kwargs):
        """
        :param namelist: Dict of reference_keys whose values are a text to be translated.
        :param lang: The full language name (not language code).
        :param namelist_id:The namelist identifier the namelist is associated with. Used for logging.
        :param available_apis: API functions to use for translation. Will be inserted in between db translation and
        machine translation methods.
        """
        self.id = kwargs.get('namelist_id')
        self.namelist = kwargs.get('namelist')
        self.namelist_length = len(self.namelist)
        available_funcs = [self.db_translate]
        available_funcs.extend([getattr(self, name) for name in kwargs.get('available_apis')])
        available_funcs.append(self.mt_easynmt)
        self.funcs = available_funcs
        self.lang = kwargs.get('lang')
        self.lang_code = c.TABLE_LANGUAGES[self.lang]
        self.translated = Queue()
        self.untranslated = Queue()
        self.is_done = False
        self.lang_table = db.get_language_dict(self.lang)
        self.translated_dict = dict()
        self.counter = 0
        self.lock = Lock()
        self.runs = 0
        self.max_runs = kwargs.get('max_runs', c.MAX_RUNS)
        self.gt_client = gtranslate.Client()

    def run(self):
        """
        Executes the translation functions in order, and will execute the loop over the function list until
        self.max_runs is met.
        :return: a dictionary of translated items. If there are untranslated words remaining after all runs. the
        original text will be returned as the value for the reference key.
        """
        while self.runs != self.max_runs:
            # seed untranslated queue with all namelist loc_key, text pairs
            for loc_key, text in self.namelist.items():
                self.untranslated.put((loc_key, text))

            # iterate over usable functions and perform cascading translation
            for func in self.funcs:
                try:
                    log.info(f'{func.__name__}() | Beginning translation of {self.id} to {self.lang}')
                    log.debug(
                        f'{func.__name__}() | Texts requiring translation for lang({self.lang_code}): {self.namelist_length}')
                    if func.__name__ not in skipped_translators:
                        func()
                    else:
                        continue
                    log.info(
                        f'{func.__name__}() | Queue State | ID: {self.id} | Lang: {self.lang_code} | Translated: {self.translated.qsize()} | Untranslated {self.untranslated.qsize()}')
                    if self.done():
                        log.info(
                            f'Translation complete! ID:{self.id} | Lang: {self.lang_code} | Num Translated: {self.namelist_length}')
                        return self.queue_to_dict()

                except IntegrityError as e:
                    if 'UniqueViolation' in str(e):
                        log.warning(f'Translated text already exists: {e}')
                        log.debug(tb.format_exc())
                    else:
                        log.error(f'Unexpected database error: {e}')
                except Exception as e:
                    log.error(f'Unexpected error occurred: {e}')
                    log.error(tb.format_exc())
                    if func.__name__ not in skipped_translators:
                        skipped_translators.add(func.__name__)
                    continue
            if self.translated.qsize() != self.namelist_length:
                log.error(
                    f'{self.runs} incomplete: translation methods exhausted with {self.untranslated.qsize()} translations remaining. Retrying run...')
            self.runs += 1

        # Translations didn't complete, but we'll put the english words back in so text will exist at least.
        while self.untranslated.qsize() > 0:
            result = self.untranslated.get()
            self.translated.put(result)
        return self.queue_to_dict()

    def increment(self):
        """
        Increments the counter the tracks the number of translated texts. Lock probably not necessary byt using it
        to be on the safe side.
        :return:
        """
        with self.lock:
            self.counter += 1

    def done(self):
        """
        Returns true if the ref_key:text pairs are done being translated.
        :return:
        """
        with self.lock:
            return self.counter == self.namelist_length

    def queue_to_dict(self):
        """
        Processes the translation queue into a dict using the same reference keys that were passed in but with
        translated texts instead of the original english ones.
        :return:
        """
        while self.translated.qsize() > 0:
            log.debug(f"Converting translation queue to dict. Queue length is {self.translated.qsize()}")
            try:
                result = self.translated.get()
                self.translated_dict[result[0]] = result[1]
            except Exception as e:
                log.critical(f'Problem processing translation queue: {e}')
        log.debug(f'Finished processing translation queue: {self.translated.qsize()} ')

    def get_remaining(self):
        """
        Process the untranslated queue into a list of untranslated terms that can be passed on to the next translation
        function in self.funcs.
        :return:
        """
        inputs = []
        while self.untranslated.qsize() > 0:
            inputs.append(self.untranslated.get())
        return inputs

    def insert_one(self, **kwargs):
        """
        Insert a translated text into the database.
        :param loc_key: the localisation key that references the translated text.
        :param detokenized: the 'detokenized' dict that carries the translated text and meta information.
        :param translators: the translator(s) used to perform the translation.
        :param translator_mode: api or mt(machine translation) mode.
        :return:
        """
        category = None
        loc_key = kwargs.get('loc_key')
        detokenized = kwargs.get('detokenized')
        for k, v in c.NAMELIST_CATEGORY_TAGS.items():
            if k in loc_key:
                category = v
        db.add_row(
            localisation_key=loc_key,
            language=self.lang,
            english=detokenized['detokenized_txt'],
            translation=detokenized['translation'],
            translators=kwargs.get('translators'),
            translator_mode=kwargs.get('translator_mode'),
            namelist_category=category,
            translation_date=datetime.datetime.now()
        )

    def db_translate(self):
        """
        Multithreaded execution of db requests to retrieve previously translated texts.
        :return: List of translated texts.
        """
        log.info(f'Getting {self.lang} translations from database')
        with ThreadPoolExecutor(max_workers=c.MAX_WORKERS,
                                thread_name_prefix=f'db_translate_{self.id}_{self.lang_code}') as executor:
            results = list(executor.map(self._do_db_translate, self.get_remaining()))
        return results

    def _do_db_translate(self, loc_kv):
        detokenized = detokenize(loc_kv[1])
        try:
            response = detokenized['translation'] = self.lang_table[loc_kv[0]]
            detokenized['translation'] = clean_input_text(response).title()
            self.translated.put((loc_kv[0], retokenize(detokenized)))
            self.increment()
        except Exception as e:
            log.warning(
                f'dbtrans: Unable to translate {loc_kv[0]} : {loc_kv[1]} : {self.lang_code}: {e}. Returning it to the queue.')
            log.debug(f'Untranslated={self.untranslated.qsize()}')
            self.untranslated.put(loc_kv)
            log.debug(f'Untranslated={self.untranslated.qsize()}')

    def api_gtrans(self):
        """
        Multithreaded execution of googletrans to translate any remaining untranslated texts.
        :return: List of translated texts.
        """
        log.info(f'Attempting translation with googletrans')
        with ThreadPoolExecutor(max_workers=c.MAX_WORKERS,
                                thread_name_prefix=f'api_gtrans_{self.id}_{self.lang_code}') as executor:
            results = list(executor.map(self._do_gtrans, self.get_remaining()))
        return results

    @sleep_and_retry
    @limits(calls=c.RATE_LIMIT_CALLS, period=c.RATE_LIMIT_INTERVAL)
    def _do_gtrans(self, loc_kv):
        try:
            if 'api_gtrans' in skipped_translators:
                log.warning(
                    f'api_gtrans is now skipped. Returning {loc_kv[0]}:{loc_kv[1]} to queue.')
                self.untranslated.put(loc_kv)
                return
            detokenized = detokenize(loc_kv[1])
            response = self.gt_client.translate(detokenized['detokenized_txt'], source_language='en',
                                                target_language=self.lang_code.replace('zh', 'zh-CN'))

            detokenized['translation'] = clean_input_text(response['translatedText']).title()
            log.debug(
                f'Queue state after translating {detokenized["translation"]}({self.lang_code}) for {self.id} : Translated: {self.translated.qsize()} | Untranslated {self.untranslated.qsize()}')
            self.translated.put((loc_kv[0], retokenize(detokenized)))
            self.increment()
            if loc_kv[0] not in self.lang_table.keys() and loc_kv[0] != 'TEST_KEY':
                log.debug(
                    f'Attempting db insertion of {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
                self.insert_one(loc_key=loc_kv[0], detokenized=detokenized, translators='gtrans', translator_mode='api')
            log.debug(
                f'Translation(gtrans:{self.lang_code}) result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
        except httpcore.ReadError as e:
            log.error(f'Unable to translate {loc_kv[0]}:{loc_kv[1]} after run {self.runs}: {e}, retrying...')
            log.debug(tb.format_exc())

        except Exception as e:
            log.error(f'Unable to translate {loc_kv[0]}:{loc_kv[1]}after run {self.runs}: {e}, retrying...')
            log.debug(tb.format_exc())

    def api_deepl(self):
        """
        Multithreaded execution of deepl to translate any remaining untranslated texts.
        :return: List of translated texts.
        """
        log.info(f'Attempting translation with deepl')
        with ThreadPoolExecutor(
                max_workers=c.MAX_WORKERS,
                thread_name_prefix=f'api_deepl_{self.id}_{self.lang_code}') as executor:
            results = list(executor.map(self._do_deepl, self.get_remaining()))
        return results

    def to_dl_code(self):
        if self.lang_code in c.DL_CODES.keys():
            return c.DL_CODES[self.lang_code]
        return self.lang_code

    def _do_deepl(self, loc_kv):
        try:
            if 'api_deepl' in skipped_translators:
                log.warning(
                    f'api_gtrans is now skipped. Returning {loc_kv[0]}:{loc_kv[1]} to queue.')
                self.untranslated.put(loc_kv)
                return
            detokenized = detokenize(loc_kv[1])
            dl = deepl.Translator(os.getenv('DEEPL_AUTH_KEY'))
            response = dl.translate_text(detokenized['detokenized_txt'], source_lang='en',
                                         target_lang=self.to_dl_code())
            detokenized['translation'] = clean_input_text(response.text).title()
            self.translated.put(loc_kv[0], retokenize(detokenized))
            self.increment()
            log.debug(
                f'Translation(deepl:{self.lang_code}) result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
            if loc_kv[0] not in self.lang_table.keys() and loc_kv[0] != 'TEST_KEY':
                self.insert_one(loc_key=loc_kv[0], detokenized=detokenized, translators='deepl', translator_mode='api')
            return loc_kv[0], detokenized
        except Exception as e:
            log.warning(f'Unable to translate {loc_kv[0]}:{loc_kv[1]}: {e}. Returning it to the queue.')
            log.debug(tb.format_exc())
            skipped_translators.add('api_deepl')
            self.untranslated.put(loc_kv)

    def api_mmt(self):
        """
        Multithreaded execution of MyMemory translation to translate any remaining untranslated texts.
        :return: List of translated texts.
        """
        log.info(f'Attempting translation with mmt')
        with ThreadPoolExecutor(max_workers=c.MAX_WORKERS,
                                thread_name_prefix=f'api_mmt_{self.id}_{self.lang_code}') as executor:
            results = list(executor.map(self._do_mmt, self.get_remaining()))
        return results

    def _do_mmt(self, loc_kv):
        try:
            if 'api_mmt' in skipped_translators:
                log.warning(
                    f'api_gtrans is now skipped. Returning {loc_kv[0]}:{loc_kv[1]} to queue.')
                self.untranslated.put(loc_kv)
                return
            detokenized = detokenize(loc_kv[1])
            url = f'https://api.mymemory.translated.net/get?q={detokenized["detokenized_txt"]}&langpair=en|{self.lang_code}'
            response = requests.get(url)
            if response.status_code == http.HTTPStatus.TOO_MANY_REQUESTS:
                content = response.json()
                log.warning(f'Daily request quota used up for MMT: {content["responseDetails"]}')
                self.untranslated.put(loc_kv)
                skipped_translators.add('_api_mmt')
                return
            if response.status_code == http.HTTPStatus.OK and loc_kv[0] != 'TEST_KEY':
                detokenized['translation'] = clean_input_text(response.json()['responseData']['translatedText']).title()
                self.insert_one(loc_key=loc_kv[0], detokenized=detokenized, translators='mmt', translator_mode='api')
                self.translated.put(loc_kv[0], retokenize(detokenized))
                self.increment()
            log.debug(
                f'Translation(mmt:{self.lang_code}) result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
            return loc_kv[0], detokenized
        except Exception as e:
            log.warning(f'Unable to translate {loc_kv[0]}:{loc_kv[1]}: {e}. Returning it to the queue.')
            log.debug(tb.format_exc())
            self.untranslated.put(loc_kv)
            skipped_translators.add('_api_mmt')

    def mt_easynmt(self):
        """
        Execution of easynmt to translate any remaining untranslated texts. Parallelism is handled by easynmt internally.
        :return: List of translated texts.
        """
        remaining = self.get_remaining()
        try:
            detokenized = [detokenize(i[1]) for i in remaining]
            for_translation = [i['detokenized_txt'] for i in detokenized]
            easynmt = EasyNMT(c.MT_MODELS[self.lang])
            log.info(
                f'Remaining {len(for_translation)} untranslated items for {self.id} will be translated with easynmt')
            response = easynmt.translate(for_translation, source_lang='en', target_lang=self.lang_code)
            for r in remaining:
                detokenized['translation']: retokenize(clean_input_text(response.pop()).title())
                self.translated.put((r[0], detokenized))
                self.insert_one(loc_key=r[0], detokenized=detokenized, translators='mmt', translator_mode='api')
                self.increment()

        except Exception as e:
            for loc_kv in remaining:
                log.warning(f'Unable to translate {loc_kv[0]}:{loc_kv[1]}: {e}. Returning it to the queue.')
                log.debug(tb.format_exc())
                self.untranslated.put(loc_kv)


def check_api_availability():
    """
    Checks the availability of certain APIs to ensure that they can be used in the function list.
    :return:
    """
    available = []
    test_phrase = 'Hello, World!'
    test_lang = 'es'

    url = f'https://api.mymemory.translated.net/get?q={test_phrase}&langpair=en|{test_lang}'
    mmt_response = requests.get(url)
    if mmt_response.status_code == http.HTTPStatus.OK:
        available.append('api_mmt')
        log.info(f'MyMemory API available for use')
    else:
        msg = mmt_response.json()['responseDetails']
        log.warning(f'MyMemory API not available for use in this run so we won\'t use it: {msg}')
    try:
        dl = deepl.Translator(os.getenv('DEEPL_AUTH_KEY'))
        dl.translate_text(test_phrase, source_lang='en', target_lang=test_lang)
        available.append('api_deepl')
        log.info(f'Deepl API available for use')
    except Exception as e:
        log.warning(f'Deepl API not available for use in this run so we won\'t use it ({e})')

    test_client = gtranslate.Client()
    gtrans_response = test_client.translate(test_phrase, target_language=test_lang)
    if gtrans_response:
        log.debug(f'Test succeeded: {gtrans_response["translatedText"]}')
        available.append('api_gtrans')
        log.info(f'Google API available for use')
    else:
        log.warning(f'Google API not available for use in this run so we won\'t use it')

    return available
