"""Get sprite 1761 frame->label (pure, no non-ascii in split anchor)."""
import sys, struct, zlib
sys.stdout = sys.stdout or __import__('io').TextIOWrapper(__import__('sys').stdout.buffer, encoding='utf-8')
exec(open(r'tools\frame_numbers.py', encoding='utf-8').read().split('ZONES')[0])

zone = sprite_labels(r'game_assets\swfs\map.swf', 1761)
print('sprite 1761 (0-based frame -> label):')
for f, l in sorted(zone.items()):
    print(f'  {f}: {l}')
