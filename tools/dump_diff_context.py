"""Dump npc_progress around difficulty_unlock records + enumerate all difficulty-related strings."""
import io, sys, sqlite3, re, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from mewgenics_core import MewgenicsSaveManager
mgr = MewgenicsSaveManager()
blob = sqlite3.connect(mgr.file_path).execute("SELECT data FROM files WHERE key='npc_progress'").fetchone()[0]

def hexdump(data, max_len=256):
    for i in range(0, min(len(data), max_len), 16):
        ch = data[i:i+16]
        print(f'  {i:04X}: {" ".join(f"{b:02X}" for b in ch):<48} {"".join(chr(b) if 32<=b<=126 else "." for b in ch)}')

# 找 difficulty_unlock_act1_hard 的偏移
pat = b'difficulty_unlock_act1_hard'
idx = blob.find(pat)
print(f'difficulty_unlock_act1_hard @ 0x{idx:X}')
# 记录以 u64 len 前缀 → 名字前 8 字节是长度
# 打印该记录前后 40 字节
start = idx - 8
print('周围 48 字节预览:')
hexdump(blob[start-8:start+48])

# 枚举所有 difficulty_unlock_* 记录（带其 u64 前缀与后续值）
print()
print('=== 所有 difficulty_unlock_* / hardpath / invasion 字符串 (含 u64 长度前缀与后续 i32) ===')
pos = 0
while pos + 8 < len(blob):
    slen = struct.unpack_from('<Q', blob, pos)[0]
    if 4 <= slen <= 60 and pos + 8 + slen <= len(blob):
        s = blob[pos+8:pos+8+slen].decode('ascii', 'ignore')
        if all(32 <= ord(c) < 127 for c in s):
            if re.search(r'(difficulty_unlock|hardpath|invasion|nightmare)', s, re.I):
                vpos = pos + 8 + slen
                v = struct.unpack_from('<i', blob, vpos)[0] if vpos+4 <= len(blob) else None
                # 也打印下一个可能 u64
                print(f'  {s:40s} next_i32={v} @0x{pos:X}')
            pos += 8 + slen
            continue
    pos += 1
