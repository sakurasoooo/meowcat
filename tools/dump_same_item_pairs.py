"""Byte-diff same-name item pairs (Ankh/D6/Neverstone/SuperheroHat) to locate the wear-state byte."""
import io, sys, os, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from mewgenics_core import MewgenicsSaveManager

mgr = MewgenicsSaveManager(); mgr.load()
blob = mgr.inventories['storage']
items = blob.items
# InventoryItem 保存了原始尾巴吗？看 core 定义——直接重解析 blob 拿原始字节更稳
raw = blob.raw  # 若无此属性则从 mgr 拿原始 blob
print('has raw:', hasattr(blob, 'raw'))

from collections import defaultdict
groups = defaultdict(list)
for idx, it in enumerate(items):
    groups[it.name].append((idx, it))

for name, lst in groups.items():
    if len(lst) < 2:
        continue
    print(f'===== {name} x{len(lst)} =====')
    for idx, it in lst:
        print(f'  [{idx}] serial={it.serial} m1={it.m1} a={it.unk_a} b={it.unk_b} f1={it.flag1:#x} f2={it.flag2:#x} extra={it.extra!r}')
