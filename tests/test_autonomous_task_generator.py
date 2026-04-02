import unittest
from tools.autonomous_task_generator import generate_autonomous_task

class TestAutonomousTaskGenerator(unittest.TestCase):
    def test_generate_autonomous_task(self):
        task = generate_autonomous_task()
        self.assertIsNotNone(task)
        self.assertIn('type', task)
        self.assertIn('target', task)
        self.assertIn('action', task)

if __name__ == '__main__':
    unittest.main()