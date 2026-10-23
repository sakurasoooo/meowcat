"""Check mgr.npc_records for difficulty_unlock + understand npc_progress record structure."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')
from mewgenics_core import MewgenicsSaveManager

mgr = MewgenicsSaveManager(); mgr.load()
recs = getattr(mgr, 'npc_records', None)
print('npc_records type:', type(recs).__name__, 'len:', len(recs) if recs else 0)
if recs:
    diff = [(k, v) for k, v in recs if 'difficulty' in k.lower() or 'invasion' in k.lower() or 'hardpath' in k.lower()]
    print('难度/入侵相关:', diff[:20])
    print()
    print('全部记录样本:', recs[:15])
