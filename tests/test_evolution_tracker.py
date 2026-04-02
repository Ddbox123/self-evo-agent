import unittest
from tools.evolution_tracker import log_evolution_tool, get_evolution_history_tool

class TestEvolutionTracker(unittest.TestCase):
    def setUp(self):
        self.file_modified = 'tools/evo_tracker_test.py'
        self.change_type = 'add'
        self.reason = 'Test addition'
        self.success = True
        self.details = 'Test details'

    def test_log_evolution_tool(self):
        result = log_evolution_tool(file_modified=self.file_modified, change_type=self.change_type, reason=self.reason, success=self.success, details=self.details)
        self.assertIn('Success', result)

    def test_get_evolution_history_tool(self):
        history = get_evolution_history_tool(limit=10)
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)

if __name__ == '__main__':
    unittest.main()