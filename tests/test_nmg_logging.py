import colorlog
import logging
import tempfile
import unittest

from namelist_mod_gen.nmg_logging.logger import Logger


class TestLogger(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = Logger(name='unit-testing', level=logging.DEBUG)

    def test_logger(self):
        print('\n')
        logger = self.logger.get_logger()
        logger.debug('This should be a gray debug message')
        logger.info('This should be a green info message')
        logger.warning('This should be a yellow warning message')
        logger.error('This should be a red error message')
        logger.critical('This should be a red a critical message')

    def test_add_file_handler(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            self.logger.add_file_handler(f.name)
            logger = self.logger.get_logger()
            logger.info('Unit Test')

        with open(f.name, 'r') as f:
            txt = f.read()
            self.assertIn('Unit Test', txt)

        # Delete the temporary file
        import os
        os.remove(f.name)
