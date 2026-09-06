import re

exe_path = r'C:\Program Files (x86)\Steam\steamapps\common\Mewgenics\Mewgenics.exe'
with open(exe_path, 'rb') as f:
    data = f.read()

# Search for "cats" table queries
sql_matches = re.findall(b'([a-zA-Z0-9_ \t\n\r*:=,<>?\'\"()]{3,80}(?:cats|furniture|properties|files)[a-zA-Z0-9_ \t\n\r*:=,<>?\'\"()]{0,80})', data)
for s in sql_matches:
    s_clean = s.decode('latin1', errors='ignore').strip()
    if any(keyword in s_clean.lower() for keyword in ['select', 'insert', 'update', 'delete', 'create', 'table', 'from', 'where']):
        print(s_clean)
