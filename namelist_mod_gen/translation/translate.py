# Should use multiprocessing pool for offline translation
# Should use thread pool for online translation
# To minimize requests for API, we should find a way to chunk translations:
import datetime
import logging
import os
import sqlite3
import asyncio
import traceback as tb
from multiprocessing.pool import ThreadPool

import deepl
import googletrans
import requests
from easynmt import EasyNMT

import constants.constants as c
from clean.cleaner import clean_input_text
from db.db import Connection
from token_handlers.handlers import detokenize, retokenize

db = Connection(db_path=c.DB_PATH, pool_size=c.DB_POOL_SIZE, max_overflow=c.DB_MAX_OVERFLOW,
                pool_timeout=c.DB_POOL_TIMEOUT)

log = logging.getLogger('NMG')

ez_nmt_model = EasyNMT('opus-mt')


class Translator(object):
    def __init__(self, namelist, lang):
        self.namelist_length = len(namelist)
        self.lang = lang
        self.lang_code = c.TABLE_LANGUAGES[lang]
        self.translated = dict()
        self.untranslated = namelist
        self.__is_done__ = False
        self.gtrans = googletrans.Translator()
        self.deepl = deepl.Translator(os.getenv('DEEPL_AUTH_KEY'))
        self.lang_table = db.get_language_dict(self.lang)
        self.loop = asyncio.get_event_loop()

    def done(self):
        self.__is_done__ = len(self.translated) == self.namelist_length and len(self.untranslated) == 0
        return self.__is_done__

    def update_untranslated(self, key):
        del self.untranslated[key]

    def translate_namelist(self):
        try:
            self.db_translate()
            if self.done():
                return self.translated

            asyncio.run(self.api_gtrans())
            if self.done():
                return self.translated

            self.api_deepl()
            if self.done():
                return self.translated

            self.api_mmt()
            if self.done():
                return self.translated

        except sqlite3.IntegrityError as e:
            log.warning(f'Translated text already exists: {e}')
            log.debug(tb.format_exc())
        except Exception as e:
            log.error(f'Unexpected error occurred: {e}')
            log.error(tb.format_exc())

    def insert_many(self, objects, translators, translator_mode, language, date):
        db.add_many(objects, translators, translator_mode, language, date)

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
        log.info('Getting translations from database')
        translated_keys = list()
        for loc_key, text in self.untranslated.copy().items():
            detokenized = detokenize(text)
            if detokenized['detokenized_txt'] in self.lang_table.keys():
                detokenized['translation'] = self.lang_table[detokenized['detokenized_txt']]
                self.translated[loc_key] = retokenize(detokenized)
                translated_keys.append(loc_key)

        for key in translated_keys:
            self.update_untranslated(key)

    async def _do_gtrans(self, input):
        detokenized = detokenize(input[1])
        result = await self.loop.run_in_executor(None, self.gtrans.translate, detokenized['detokenized_txt'], self.lang_code.replace('zh', 'zh-CN'))
        detokenized['translation'] = clean_input_text(result.text).title()
        self.translated[input[0]] = retokenize(detokenized)
        log.debug(f'Translation result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
        self.insert_one(loc_key=input[0], detokenized=detokenized, translators='gtrans', translator_mode='api')

    async def api_gtrans(self):
        log.info(f'Attempting translation with googletrans')
        tasks = []
        for key, value in self.untranslated.items():
            task = asyncio.ensure_future(self._do_gtrans((key, value)))
            tasks.append(task)
        await asyncio.gather(*tasks)

        for loc_key in self.untranslated.keys():
            self.update_untranslated(loc_key)

    def _do_deepl(self, input):
        detokenized = detokenize(input[1])
        result = self.deepl.translate_text(detokenized['detokenized_txt'], target_lang=self.lang_code)
        detokenized['translation'] = clean_input_text(result.text).title()
        self.translated[input[0]] = retokenize(detokenized)
        log.debug(f'Translation result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
        self.insert_one(loc_key=input[0], detokenized=detokenized, translators='gtrans', translator_mode='api')

    def api_deepl(self):
        log.info(f'Attempting translation with googletrans')
        with ThreadPool(c.THREAD_CONCURRENCY) as pool:
            pool.map(self._do_deepl, self.untranslated.items())

        for loc_key in self.untranslated.keys():
            self.update_untranslated(loc_key)

    def _do_mmt(self, input):
        detokenized = detokenize(input[1])
        url = f'https://api.mymemory.translated.net/get?q={detokenized["detokenized_txt"]}&langpair=en|{self.lang_code}'
        result = requests.get(url)
        detokenized['translation'] = clean_input_text(result.text).title()
        self.translated[input[0]] = retokenize(detokenized)
        log.debug(f'Translation result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
        self.insert_one(loc_key=input[0], detokenized=detokenized, translators='gtrans', translator_mode='api')

    def api_mmt(self):
        log.info(f'Attempting translation with googletrans')
        with ThreadPool(c.THREAD_CONCURRENCY) as pool:
            pool.map(self._do_mmt, self.untranslated.items())

        for loc_key in self.untranslated.keys():
            self.update_untranslated(loc_key)

    def _do_easynmt(self, input):
        detokenized = detokenize(input[1])
        result = ez_nmt_model.translate(detokenized['detokenized_txt'], source_lang='en', target_lang=self.lang_code)
        detokenized['translation'] = clean_input_text(result.text).title()
        self.translated[input[0]] = retokenize(detokenized)
        log.debug(f'Translation result: {detokenized["detokenized_txt"]} -> {detokenized["translation"]}')
        self.insert_one(loc_key=input[0], detokenized=detokenized, translators='gtrans', translator_mode='api')

    def mt_easynmt(self):
        log.info(f'Attempting translation with googletrans')
        with ThreadPool(c.THREAD_CONCURRENCY) as pool:
            pool.map(self._do_easynmt, self.untranslated.items())

        for loc_key in self.untranslated.keys():
            self.update_untranslated(loc_key)
