"""Search the ENTIRE save for difficulty/invasion/hardpath progress markers."""
import io, sys, sqlite3, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from mewgenics_core import MewgenicsSaveManager

mgr = MewgenicsSaveManager()
p = mgr.file_path
conn = sqlite3.connect(p)
cur = conn.cursor()

# 所有表与 blob 里找 difficulty/hardpath/invasion 相关字符串
pat = re.compile(r'(hardpath|HardPath|invasion|Invasion|diff_|difficulty|nightmare|NIGHTMARE|impossible|INFESTATION)', re.I)
print('=== 扫描所有 blob 中的难度/入侵关键词 ===')
for (tbl,) in cur.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    try:
        cols = [r[1] for r in cur.execute(f'PRAGMA table_info({tbl})')]
        if 'data' in cols or 'blob' in cols:
            for (key,) in cur.execute(f'SELECT key FROM {tbl} LIMIT 2000'):
                pass
    except Exception:
        pass

# 直接遍历 files 表的所有 blob
for (key, data) in cur.execute("SELECT key, data FROM files"):
    if not data:
        continue
    for m in re.finditer(rb'[\x20-\x7e]{4,40}', data):
        s = m.group().decode('ascii', 'ignore')
        if pat.search(s) and not s.startswith('.'):
            print(f'  files/{key}: {s}')

# 属性里找
print()
print('=== properties 里的难度/hardpath 标志 ===')
for k, v in sorted(mgr.properties.items()):
    if pat.search(str(k)):
        print(' ', k, '=', v)

conn.close()
