"""Inspect wiki achievements data & find achievement icon source."""
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    a = json.load(open('wiki_data/achievements_tables.json', encoding='utf-8'))
    print('type', type(a).__name__)
    s = json.dumps(a, ensure_ascii=False)
    # 找 icon 相关字段名
    keys = set(re.findall(r'"([A-Za-z_]*(?:icon|Image|frame|sprite)[A-Za-z_]*)"', s))
    print('icon-ish keys:', keys)
    print('总长度:', len(s))
    # 展示第一个条目
    def first(o, depth=0):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (str, int, bool)):
                    print(' ', k, '=', str(v)[:70])
                elif isinstance(v, (dict, list)) and depth < 4:
                    first(v, depth + 1)
        elif isinstance(o, list) and o:
            first(o[0], depth + 1)
    first(a)
except Exception as e:
    print('ERR', e)
