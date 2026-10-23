"""Smoke test for the 15-slot left/right mutation model (read-only against save)."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from mewgenics_core import MewgenicsSaveManager, CatRecord

mgr = MewgenicsSaveManager(); mgr.load()
cats = mgr.cats

def find(name):
    return next((c for c in cats.values() if c.name == name), None)

print('=== Nicholas (右腿变异 418) ===')
c = find('Nicholas')
print('legs L/R:', c.mutations['legs'], '/', c.right_mutations['legs'])
print('counts:', c.mutation_counts())
mods = c.mutation_stat_modifiers
print('stat mods (应含 legs418 的 -1con/+2int):', {k: v for k, v in mods.items() if v})

print()
print('=== 214 (左臂缺失 -2, 右臂 314) ===')
c = find('214')
print('arms L/R:', c.mutations['arms'], '/', c.right_mutations['arms'])
print('counts (缺失算出生缺陷):', c.mutation_counts())

print()
print('=== Dev (编辑器造的全满猫，应 15 变异 0 不对称) ===')
c = find('Dev')
print('counts:', c.mutation_counts())
mods = c.mutation_stat_modifiers
print('stat mods 合计:', sum(mods.values()), {k: v for k, v in mods.items() if v})

print()
print('=== set_right_mutation 写字节验证 ===')
c = find('Nicholas')
before = bytes(c.parts_chunk)
c.set_right_mutation('legs', 1500)  # 0x05DC: 与 418(0x01A2) 低两字节均不同
after = bytes(c.parts_chunk)
diffs = [i for i in range(len(before)) if before[i] != after[i]]
print('right=1500 后变化字节:', diffs, '(应只在 184~185)')
assert diffs == [184, 185], 'offset wrong!'
import struct
print('off2 现在的值:', struct.unpack_from('<i', c.parts_chunk, 184)[0])
print('counts now:', c.mutation_counts())
c.set_right_mutation('legs', 418)  # restore in memory only
assert bytes(c.parts_chunk) == before
print('恢复后字节一致 ✓')

# 全档一致性：所有猫可解析且计数不报错
n_mut = n_def = 0
for c in cats.values():
    cnt = c.mutation_counts()
    n_mut += cnt['mutations']; n_def += cnt['birth_defects']
print(f'\n675 猫合计: 变异部件 {n_mut}, 出生缺陷部件 {n_def}')
print('ALL OK')
