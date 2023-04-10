# Generated with help from ChatGPT

import unittest

from namelist_mod_gen.clean.cleaner import clean_input_text


class TestCleaner(unittest.TestCase):
    def test_clean_input_text(self):
        test_cases = {
            "foo": "foo",  # basic test case
            " Foo\tBar\t": "FooBar",  # test case with leading/trailing whitespace and tabs
            "Dave's car\n": "Dave's car",  # test case with a newline character
            "\x00\x1F\x7F\x9F": "",  # test case with only control characters
            "hello\x0Bworld": "helloworld",  # test case with a vertical tab character
            "\t\n\r ": "",  # test case with only whitespace characters
            "\u200bfoo\u200b": "foo",  # test case with a zero-width space character
            "\u202ffoo\u202f": "foo",  # test case with a narrow no-break space character
            "foo\uFEFF": "foo",  # test case with a byte order mark (BOM) character
            "foo\ufeff": "foo",  # test case with a small form variant (SFV) of BOM character
        }

        for test, expectation in test_cases.items():
            self.assertEqual(expectation, clean_input_text(test))
