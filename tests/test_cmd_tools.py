import unittest
from tools.cmd_tools import run_cmd_tool

class TestCmdTools(unittest.TestCase):
    def test_run_cmd_tool(self):
        result = run_cmd_tool(command='echo Hello, World!')
        self.assertIn('Hello, World!', result)

if __name__ == '__main__':
    unittest.main()