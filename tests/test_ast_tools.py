import unittest
from tools.ast_tools import get_code_entity, list_file_entities

class TestAstTools(unittest.TestCase):
    def setUp(self):
        self.file_path = 'tools/ast_tools.py'

    def test_get_code_entity(self):
        entity = get_code_entity(self.file_path, 'get_code_entity')
        self.assertIsNotNone(entity)

    def test_list_file_entities(self):
        entities = list_file_entities(self.file_path)
        self.assertIsInstance(entities, list)
        self.assertGreater(len(entities), 0)

if __name__ == '__main__':
    unittest.main()