# Generated with help from ChatGPT

import unittest
from datetime import datetime

from namelist_mod_gen.db.db import Connection, Translation
from sqlalchemy import inspect


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.connection = Connection(':memory:')

    def tearDown(self):
        self.connection = None

    def test_create_tables(self):
        inspector = inspect(self.connection.engine)
        self.assertTrue(inspector.has_table('translations'))

    def test_add_row(self):
        with self.connection.session_scope() as session:
            self.connection.add_row(localisation_key='loc_key 1', english='hello', translation='bonjour',
                                    translators='translator1', language='french',
                                    translator_mode='mode1', namelist_category='category1',
                                    translation_date=datetime.now())
            self.assertEqual(session.query(Translation).first().translation, 'bonjour')

    def test_get_language_dict(self):
        self.connection.add_row(localisation_key='loc_key 1', english='hello', translation='bonjour',
                                translators='translator1', language='french',
                                translator_mode='mode1', namelist_category='category1',
                                translation_date=datetime.now())
        french_dict = self.connection.get_language_dict('french')
        self.assertEqual(french_dict, {'hello': 'bonjour'})


if __name__ == '__main__':
    unittest.main()
