import unittest


class TestSomePackage(unittest.TestCase):
    @unittest.skip('this is a template for creating other unit tests')
    def test_some_function(self):
        """
        In test cases, the key should be the test case and the value the expected case
        :return:
        """
        test_cases = {
            "": ""
        }
        for test, expectation in test_cases.items():
            self.assertEqual(test, expectation)
