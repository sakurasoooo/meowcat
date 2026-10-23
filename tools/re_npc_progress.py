"""Reverse-engineer npc_progress blob structure."""
import sqlite3, os, sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = os.path.expandvars(r'%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav')
data = sqlite3.connect(p).execute("SELECT data FROM files WHERE key='npc_progress'").fetchone()[0]
print(f'total {len(data)} bytes')
print('head:', data[:64].hex())

def hexdump(d, off, n):
    for i in range(off, min(off+n, len(d)), 16):
        chunk = d[i:i+16]
        print(f'{i:05X}: {" ".join(f"{b:02X}" for b in chunk):<48} {"".join(chr(b) if 32<=b<=126 else "." for b in chunk)}')

hexdump(data, 0, 160)

# try: u32 npc_count, then per npc: u64 len + name, ...
count = struct.unpack_from('<I', data, 0)[0]
print(f'\npossible npc count = {count}')
off = 4
for i in range(min(count, 8)):
    nlen = struct.unpack_from('<Q', data, off)[0]
    name = data[off+8:off+8+nlen].decode('ascii', errors='replace')
    off += 8 + nlen
    print(f'npc[{i}] = {name!r} @ next={off}')
    # after name: what follows? maybe u32 count of completed sequences
    sc = struct.unpack_from('<I', data, off)[0]
    print(f'  seq_count? = {sc}')
    hexdump(data, off, min(48, 8+sc*40))
    off += 4
    # try reading sc strings
    for j in range(min(sc, 6)):
        slen = struct.unpack_from('<Q', data, off)[0]
        s = data[off+8:off+8+slen].decode('ascii', errors='replace')
        print(f'    seq[{j}] = {s!r}')
        off += 8 + slen
        # maybe trailing counters per seq
    print()
