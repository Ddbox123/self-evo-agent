import unittest
from tools.search_tools import grep_search_tool, find_function_calls_tool, find_definitions_tool

class TestSearchTools(unittest.TestCase):
    def setUp(self):
        self.regex_pattern = 'def test_'
        self.function_name = 'test_function'
        self.symbol_name = 'test_symbol'

    def test_grep_search_tool(self):
        result = grep_search_tool(regex_pattern=self.regex_pattern)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_find_function_calls_tool(self):
        result = find_function_calls_tool(function_name=self.function_name)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 2)

    def test_find_definitions_tool(self):
        result = find_definitions_tool(symbol_name=self.symbol_name)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

if __name__ == '__main__':
    unittest.main()