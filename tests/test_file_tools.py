import unittest
from tools.file_tools import read_local_file_tool, edit_local_file_tool, create_new_file_tool, list_directory_tool

class TestFileTools(unittest.TestCase):
    def setUp(self):
        self.test_file_path = 'tests/test_file.txt'
        self.content = 'This is a test file.'

    def test_read_local_file_tool(self):
        result = read_local_file_tool(file_path=self.test_file_path)
        self.assertIn('This is a test file.', result)

    def test_edit_local_file_tool(self):
        edit_local_file_tool(file_path=self.test_file_path, search_string='test file', replace_string='test file edited')
        result = read_local_file_tool(file_path=self.test_file_path)
        self.assertIn('test file edited', result)

    def test_create_new_file_tool(self):
        create_new_file_tool(file_path='tests/new_test_file.txt', content='New test file content')
        result = read_local_file_tool(file_path='tests/new_test_file.txt')
        self.assertIn('New test file content', result)

    def test_list_directory_tool(self):
        result = list_directory_tool(path='tests/')
        self.assertIn('test_file.txt', result)

if __name__ == '__main__':
    unittest.main()