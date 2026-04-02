import unittest
from tools.memory_tools import read_memory_tool, commit_compressed_memory_tool

class TestMemoryTools(unittest.TestCase):
    def setUp(self):
        self.new_core_context = 'New core context summary'
        self.next_goal = 'Next specific task'

    def test_read_memory_tool(self):
        result = read_memory_tool()
        self.assertIn('generation', result)
        self.assertIn('core_context', result)
        self.assertIn('current_goal', result)

    def test_commit_compressed_memory_tool(self):
        result = commit_compressed_memory_tool(new_core_context=self.new_core_context, next_goal=self.next_goal)
        self.assertIn('Success', result)

if __name__ == '__main__':
    unittest.main()