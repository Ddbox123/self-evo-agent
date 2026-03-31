import chardet
import sys

# 尝试检测文件编码
def detect_encoding(file_path):
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # 读取前10KB
        result = chardet.detect(raw_data)
        return result['encoding'] or 'utf-8'
    except Exception as e:
        return f'error: {e}'

if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        encoding = detect_encoding(file_path)
        print(f'File: {file_path}')
        print(f'Detected encoding: {encoding}')
    else:
        print('Usage: python diagnose_encoding.py <file_path>')