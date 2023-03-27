import unittest
from datetime import datetime

from sqlalchemy import inspect

from constants.constants import LANGUAGES
from namelist_mod_gen.db.db import Connection, French


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.connection = Connection(':memory:')

    def tearDown(self):
        self.connection = None

    def test_create_tables(self):
        inspector = inspect(self.connection.engine)
        for language in LANGUAGES.values():
            self.assertTrue(inspector.has_table(language))

    def test_add_row(self):
        with self.connection.session_scope() as session:
            self.connection.add_row(French, english='hello', translation='bonjour', translators='translator1',
                                    translator_mode='mode1', namelist_category='category1',
                                    translation_date=datetime.now())
            result = session.query(French).filter_by(english='hello').first()
            self.assertEqual(result.translation, 'bonjour')

    def test_get_language_dict(self):
        self.connection.add_row(French, english='hello', translation='bonjour', translators='translator1',
                                translator_mode='mode1', namelist_category='category1',
                                translation_date=datetime.now())
        french_dict = self.connection.get_language_dict('french')
        self.assertEqual(french_dict, {'hello': 'bonjour'})


if __name__ == '__main__':
    unittest.main()
