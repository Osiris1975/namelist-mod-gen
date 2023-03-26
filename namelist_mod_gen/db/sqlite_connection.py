import copy
import sqlite3

import constants.constants as c


class Connection:
    def __init__(self):
        try:
            self.reader = sqlite3.connect(c.DB_PATH, timeout=15, isolation_level=None)
            self.writer = sqlite3.connect(c.DB_PATH, timeout=15, isolation_level=None)
            self.reader.execute('pragma journal_mode=wal;')
            self.writer.execute('pragma journal_mode=wal;')
            self.reader.row_factory = sqlite3.Row
        except Exception as e:
            raise RuntimeError(f"Error creating connection: {str(e)}")

    def get_language_dict(self, language):
        try:
            result = self.get_language_table(language)
            return {dict(r)['english']: dict(r) for r in result}
        except Exception as e:
            raise RuntimeError(f"Error getting language dict for {language}: {str(e)}")

    def get_language_table(self, language):
        try:
            cur = self.reader.cursor()
            cur.execute(f'select * from {language};')
            return cur.fetchall()
        except Exception as e:
            raise RuntimeError(f"Error getting language table for {language}: {str(e)}")

    def create_tables(self):
        try:
            langs = copy.copy(c.LANGUAGES)
            lang_list = list(langs.values()).remove('english')
            for lang in lang_list:
                query = f"CREATE TABLE IF NOT EXISTS {lang} (english varchar, translation varchar, translators varchar, translator_mode vatchar, namelist_category varchar translation_date datetime, PRIMARY_KEY(english))"
                cur = self.reader.cursor()
                cur.execute(query)
        except Exception as e:
            raise RuntimeError(f"Error creating tables: {str(e)}")
