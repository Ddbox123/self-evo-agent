import unittest
from tools.advanced_compressor import AdvancedCompressor

class TestAdvancedCompressor(unittest.TestCase):
    def setUp(self):
        self.compressor = AdvancedCompressor()

    def test_compress_data(self):
        data = b'Hello, World!'
        compressed_data = self.compressor.compress(data)
        self.assertTrue(len(compressed_data) < len(data))

if __name__ == '__main__':
    unittest.main()