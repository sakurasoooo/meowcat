"""Check passive catalog naming vs SWF labels + icon file presence for ThouShaltNotKill."""
import io, sys, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pas_cat = json.load(open('assets/passives_catalog.json', encoding='utf-8'))
print('passive catalog entries:', len(pas_cat))
print('keys sample:', [e['key'] for e in pas_cat[:12]])
# 找 thou
for e in pas_cat:
    if 'thou' in str(e).lower():
        print('THOU entry:', json.dumps(e, ensure_ascii=False)[:200])
# 关键：这些 key 的 icon 文件
for e in pas_cat:
    if 'thou' in str(e).lower():
        fp = os.path.join('assets/icons/passives', e['key'] + '.png')
        print(f"  file exists for key [{e['key']}]: {os.path.exists(fp)}")
# 检查 has_icon flag 与文件一致
missing_file_but_flag = [e['key'] for e in pas_cat if e.get('has_icon') is False and not os.path.exists(os.path.join('assets/icons/passives', e['key'] + '.png'))]
print('has_icon=false 且文件缺失:', len(missing_file_but_flag))
print('其中 THOU:', [k for k in missing_file_but_flag if 'thou' in k.lower()])
print()
# 列出全部 has_icon=false 的被动 key
nofile = [e['key'] for e in pas_cat if not os.path.exists(os.path.join('assets/icons/passives', e['key'] + '.png'))]
print('文件缺失的被动 key 总数:', len(nofile))
print(nofile)
