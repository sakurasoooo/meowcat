"""Byte-diff same-name item pairs from the raw blob: locate the wear-state byte."""
import io, sys, os, struct, sqlite3
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from mewgenics_core import MewgenicsSaveManager, InventoryItem

mgr = MewgenicsSaveManager(); mgr.load()
p = mgr.file_path
raw = sqlite3.connect(p).execute("SELECT data FROM files WHERE key='inventory_storage'").fetchone()[0]

# re-parse keeping spans
count = struct.unpack_from('<I', raw, 0)[0]
off = 4
entries = []
for _ in range(count):
    start = off
    it, off = InventoryItem.parse(raw, start)
    entries.append((it, raw[start:off]))
print(f'{len(entries)} entries, blob {len(raw)} bytes, parsed end={off}')

from collections import defaultdict
groups = defaultdict(list)
for i, (it, bs) in enumerate(entries):
    groups[it.name].append((i, it, bs))

FIELD_RANGES = [('head_type', 0, 4), ('head_flag', 4, 5), ('namelen', 5, 13)]
def fields_of(bs):
    """yield (label, slice, value-hex) covering the whole entry."""
    nlen = struct.unpack_from('<Q', bs, 5)[0]
    p = 13
    yield ('name', slice(p, p + nlen), bs[p:p+nlen].decode())
    p += nlen
    n2 = struct.unpack_from('<Q', bs, p)[0]
    if n2 and 1 <= n2 <= 64:
        yield ('extra_len', slice(p, p+8), str(n2))
        yield ('extra', slice(p+8, p+8+n2), bs[p+8:p+8+n2].decode())
        p += 8 + n2
    else:
        yield ('zeros8', slice(p, p+8), bs[p:p+8].hex())
        p += 8
    tail = bs[p:]
    labels = ['m1', 'unk_a', 'unk_b', 'serial', 'f1', 'f2']
    sizes = [4, 4, 4, 4, 1, 1]
    q = 0
    for lb, sz in zip(labels, sizes):
        yield (lb, slice(p+q, p+q+sz), tail[q:q+sz].hex())
        q += sz

for name, lst in groups.items():
    if len(lst) < 2:
        continue
    print(f'\n===== {name} x{len(lst)} =====')
    base_i, base_it, base_bs = lst[0]
    for i, it, bs in lst:
        marks = []
        for label, sl, val in fields_of(bs):
            marks.append(f'{label}={val}')
        print(f'  [{i}] ' + ' '.join(marks))
    # diff against first
    for i, it, bs in lst[1:]:
        diffs = [(label, dict_fields[label], dict_fields2[label]) for dict_fields, dict_fields2 in [(
            {label: val for label, sl, val in fields_of(base_bs)},
            {label: val for label, sl, val in fields_of(bs)})] for label in dict_fields
            if dict_fields[label] != dict_fields2[label]]
        print(f'  [{base_i}] vs [{i}] 差异字段: ' + (', '.join(f'{a}: {b} != {c}' for a, b, c in diffs) or '(完全一致除了相对位置)'))
