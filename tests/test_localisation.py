import unittest


class TestSomePackage(unittest.TestCase):
    def test_localize_namelist(self):
        """
        In test cases, the key should be the test case and the value the expected case
        :return:
        """
        test_cases = {
            "": ""
        }
        for test, expectation in test_cases.items():
            self.assertEqual(test, expectation)
