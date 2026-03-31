import chardet
import sys

def detect_encoding(file_path):
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)
        result = chardet.detect(raw_data)
        encoding = result['encoding'] or 'utf-8'
        # 检查 BOM
        if raw_data.startswith(b'\xef\xbb\xbf'):
            encoding = 'utf-8-sig'
        elif raw_data.startswith(b'\xff\xfe'):
            encoding = 'utf-16-le'
        elif raw_data.startswith(b'\xfe\xff'):
            encoding = 'utf-16-be'
        return encoding
    except Exception as e:
        return f'error: {e}'

if __name__ == '__main__':
    file_path = 'agent.py'
    encoding = detect_encoding(file_path)
    print(f'Detected encoding for {file_path}: {encoding}')
    # 尝试用检测到的编码读取并打印前几行
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            lines = f.readlines()[:5]
        print('First 5 lines:')
        for i, line in enumerate(lines, 1):
            print(f'{i}: {line.rstrip()}')
    except Exception as e:
        print(f'Failed to read with encoding {encoding}: {e}')
