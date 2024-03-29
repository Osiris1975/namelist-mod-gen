# Generated with help from ChatGPT

import os
import shutil
import tempfile
import unittest

from namelist_mod_gen.file_handlers.paths import nl_csv_files, make_mod_directories
from namelist_mod_gen.file_handlers.txt import namelist_txt_to_dict
from namelist_mod_gen.file_handlers.writers import write_csv_from_dict


class TestCsvFiles(unittest.TestCase):
    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp()
        self.csv_file = os.path.join(self.test_dir, 'test.csv')
        with open(self.csv_file, 'w') as f:
            f.write('header1,header2,header3\n')
            f.write('value1,value2,value3\n')
        self.non_csv_file = os.path.join(self.test_dir, 'test.txt')
        with open(self.non_csv_file, 'w') as f:
            f.write('this is not a CSV file')
        self.mod_name = 'test_mod'
        self.expected_dirs = {
            "namelist": os.path.join(self.test_dir, self.mod_name, 'common', 'name_lists'),
            "localisation": [
                os.path.join(self.test_dir, self.mod_name, 'localisation', lang, 'name_lists') for lang in
                ['english', 'spanish']
            ]
        }

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir)

    def test_nl_csv_files(self):
        files = list(nl_csv_files(self.test_dir))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], os.path.abspath(self.csv_file))

    def test_nl_csv_files_non_csv(self):
        files = list(nl_csv_files(self.test_dir))
        self.assertNotIn(os.path.abspath(self.non_csv_file), files)

    def test_make_mod_directories(self):
        dirs = make_mod_directories(self.mod_name, self.test_dir)

        for k, v in self.expected_dirs.items():
            if k == "localisation":
                for i, dir_path in enumerate(v):
                    self.assertTrue(os.path.exists(dir_path))
            else:
                self.assertTrue(os.path.exists(v))


class TestTxt(unittest.TestCase):
    def test_read_namelist(self):
        """
        In test cases, the key should be the test case and the value the expected case
        :return:
        """
        test_file = 'fixtures/txt/test_us_namelist.txt'
        csv_out = 'output/test_us_namelist.csv'
        nld = namelist_txt_to_dict(test_file, 'test_author', 'Test NL', 'test_nl')
        write_csv_from_dict(csv_out, nld)
