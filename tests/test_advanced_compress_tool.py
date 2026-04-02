import unittest
from tools.advanced_compress_tool import compress_data

class TestAdvancedCompressTool(unittest.TestCase):
    def test_compress_data(self):
        data = b'Hello, World!'
        compressed_data = compress_data(data)
        self.assertTrue(len(compressed_data) < len(data))

if __name__ == '__main__':
    unittest.main()