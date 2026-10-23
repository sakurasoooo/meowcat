"""Parse npc_progress for ALL difficulty/invasion unlock records + house_boss_difficulty."""
import io, sys, sqlite3, os, re, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from mewgenics_core import MewgenicsSaveManager

mgr = MewgenicsSaveManager()
p = mgr.file_path
blob = sqlite3.connect(p).execute("SELECT data FROM files WHERE key='npc_progress'").fetchone()[0]

# npc_progress 的记录格式：u64 len + name，然后跟数值（count/i32）。用与 shop 一致的方式提取 name->value
# 先看结构：把可打印字符串序列带偏移打印
print('=== npc_progress 里 difficulty/hardpath/invasion 相关记录 ===')
# 尝试按 u64 len + string 走
off = 0
found = []
while off + 8 < len(blob):
    slen = struct.unpack_from('<Q', blob, off)[0]
    if 4 <= slen <= 80 and off + 8 + slen <= len(blob):
        s = blob[off+8:off+8+slen].decode('ascii', errors='ignore')
        if all(32 <= ord(c) < 127 for c in s):
            # 尝试读紧随的一个 i32（count/value）或 u64
            vpos = off + 8 + slen
            v = struct.unpack_from('<i', blob, vpos)[0] if vpos + 4 <= len(blob) else None
            if re.search(r'(difficulty|hardpath|hard_path|invasion|boss_difficulty)', s, re.I):
                found.append((s, v, off))
            off = vpos  # 假设每条记录长 = 名字段 + 4~8 字节值
            continue
    off += 1

for s, v, o in found:
    print(f'  {s:40s} value={v} @ {hex(o)}')

print()
print('=== properties 难度相关 ===')
for k in sorted(mgr.properties):
    if re.search(r'(difficulty|hardpath|invasion|boss)', k, re.I):
        print(' ', k, '=', mgr.properties[k])
