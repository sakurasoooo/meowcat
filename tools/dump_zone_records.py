"""Dump class_zone_records + scan npc_progress/properties for difficulty data."""
import io, sys, sqlite3, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from mewgenics_core import MewgenicsSaveManager, parse_class_zone_records

mgr = MewgenicsSaveManager(); mgr.load()

print('=== class_zone_records (cls, zone) -> (a, b, visits) ===')
rows = mgr.class_zone_records
# 按 zone 分组显示
for (cls, zone), (a, b, visits) in sorted(rows.items()):
    mark = '★通关' if a == -1 else '·'
    bmark = f' b={b}' if b != -1 else ''
    print(f'  {cls:14s} {zone:12s} {mark} visits={visits}{bmark}')

# 各 zone 的 b 分布
from collections import defaultdict, Counter
byzone = defaultdict(list)
for (cls, zone), (a, b, v) in rows.items():
    byzone[zone].append((b, a, v))
print()
print('=== 各 zone 的 b 值出现情况 (b!=-1) ===')
for zone, lst in byzone.items():
    bs = [b for b, a, v in lst if b != -1]
    if bs:
        print(f'  {zone:12s} b值分布: {Counter(bs).most_common()}')

# 扫描属性/文件 里 difficulty 关键词
print()
print('=== properties 里 difficulty 相关 ===')
for k in sorted(mgr.properties):
    if re.search(r'diff|diffi|hard|crazy|impossible|nightmare', k, re.I):
        print(' ', k, '=', mgr.properties[k])

# npc_progress 原始
print()
for box in ['npc_progress']:
    d = sqlite3.connect(mgr.file_path).execute("SELECT data FROM files WHERE key='npc_progress'").fetchone()
    if d:
        blob = d[0]
        # 找 difficulty 相关 ascii
        strs = set(re.findall(rb'[\x20-\x7e]{5,40}', blob))
        hits = [s.decode() for s in strs if re.search(r'diff|hard|crazy|imposs', s.decode(), re.I)]
        print('npc_progress 里 difficulty 相关字符串:', hits[:20])
