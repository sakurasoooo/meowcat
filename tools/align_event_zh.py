"""从汉化补丁 combined.csv 抽出事件相关中文，写入 wiki_data/event_zh.json。

覆盖：
  - 全部 EVENT_* / QEVENT_*（含 gon 里按进度/章节切换的开场）
  - 事件奖惩里会查到的道具/被动/技能/疾病名称键
"""
import csv
import json
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CANDIDATES = [
    os.environ.get('MEW_ZH_CSV') or '',
    os.path.join(ROOT, 'tools', '_zh_tmp', 'rainzz_combined.csv'),
    os.path.join(ROOT, 'tools', '_zh_tmp', 'mewcodex_combined.csv'),
    os.path.join(ROOT, 'tools', '_zh_mewcodex', 'Mewgenics_CN_patch', 'data', 'text', 'combined.csv'),
    os.path.join(ROOT, 'game_assets', 'data', 'text', 'combined.csv'),
]
OFFICIAL = next((p for p in _CANDIDATES if p and os.path.exists(p)), '')
if not OFFICIAL:
    raise SystemExit('找不到 combined.csv，请设置 MEW_ZH_CSV')

rows = list(csv.reader(open(OFFICIAL, encoding='utf-8-sig', newline='')))
header = [h.strip().lower() for h in rows[0]]
zh_i = next(header.index(c) for c in ('zh', 'zh-cn', 'schinese') if c in header)
csv_zh = {}
for r in rows[1:]:
    if not r or not r[0] or r[0].startswith('//') or len(r) <= zh_i:
        continue
    zh = (r[zh_i] or '').strip()
    if zh:
        csv_zh[r[0]] = zh

NAME_PREFIXES = (
    'ARMOR_', 'ITEM_', 'PASSIVE_', 'ABILITY_', 'DISORDER_',
    'EVENT_', 'QEVENT_',
)


def keep_key(key):
    if key.startswith('EVENT_') or key.startswith('QEVENT_'):
        return True
    if not key.endswith('_NAME'):
        return False
    return key.startswith(NAME_PREFIXES)


overlay = {k: csv_zh[k] for k in sorted(csv_zh) if keep_key(k)}
out_path = os.path.join(ROOT, 'wiki_data', 'event_zh.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(overlay, f, ensure_ascii=False, indent=2)
    f.write('\n')

n_event = sum(1 for k in overlay if k.startswith('EVENT_') or k.startswith('QEVENT_'))
n_name = len(overlay) - n_event
print(f'{OFFICIAL}')
print(f'overlay {len(overlay)}  event/qevent {n_event}  names {n_name}')
print(f'wrote {out_path}  {os.path.getsize(out_path)} bytes')
