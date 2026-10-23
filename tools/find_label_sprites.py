"""从 ffdec dump 中定位 FrameLabel 所属的 sprite chid 与帧号。"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
lines = open('_dump_ui.txt', encoding='utf-8', errors='replace').read().splitlines()
cur_sprite = None
targets = {'caves', 'boneyard', 'core', 'moon', 'jurassic', 'theend', 'meatworld', 'dimensionx', 'endoftime',
           'Fighter', 'Tank', 'Hunter', 'Thief', 'Mage', 'Medic', 'Colorless', 'Psychic', 'Jester',
           'Tinkerer', 'Butcher', 'Druid', 'Monk', 'Necromancer',
           'collars', 'cleared0', 'cleared1', 'cleared2', 'cleared3',
           'undefeated', 'defeated0', 'defeated1', 'defeated2', 'defeated3', 'incomplete'}
for ln in lines:
    m = re.search(r'DefineSprite \(chid: (\d+)\)', ln)
    if m:
        cur_sprite = m.group(1)
        continue
    m2 = re.search(r'FrameLabel \(name: "([^"]+)"\)', ln)
    if m2 and m2.group(1) in targets:
        fr = re.search(r'(\d+)\. FrameLabel', ln)
        print(f'sprite={cur_sprite}  frame={fr.group(1) if fr else "?"}  label={m2.group(1)}')
