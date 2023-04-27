# Generated with help from ChatGPT

import unittest

from validation.validation import pi_validate


class TestValidation(unittest.TestCase):

    def test_pi_validate(self):
        """
        In test cases, the key should be the test case and the value the expected case
        :return:
        """
        test_cases = {
            "Foo bar baz": 0,  # valid string with no invalid characters
            "Foo „ baz": 1,  # string with invalid namelist character („)
            "„“‚‘–”’…—": 1,  # string with multiple invalid namelist characters
            "„“‚‘–”’…—" * 50: 2,  # string with invalid characters and length > 50
            "": 0,  # empty string
            "a" * 50: 0,  # string with 50 "a" characters
            "𝐖𝐢𝐤𝐢𝐩𝐞𝐝𝐢𝐚": 1,  # string with non-Latin characters
            "Foo bar\tbaz": 0,  # string with whitespace characters
        }

        for test, expectation in test_cases.items():
            self.assertEqual(expectation, len(pi_validate(test)))
