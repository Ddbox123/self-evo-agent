import codecs

# 读取文件并移除 BOM
with open('tools/cmd_tools.py', 'rb') as f:
    content = f.read()

# 移除 UTF-8 BOM
if content.startswith(b'\xef\xbb\xbf'):
    content = content[3:]

# 写回文件
with open('tools/cmd_tools.py', 'wb') as f:
    f.write(content)

print('BOM 移除完成')