"""列出 sprite 3757 内的所有 FrameLabel。"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
lines = open('_dump_ui.txt', encoding='utf-8', errors='replace').read().splitlines()
inside = False
for ln in lines:
    m = re.search(r'DefineSprite \(chid: (\d+)\)', ln)
    if m:
        inside = (m.group(1) == sys.argv[1] if len(sys.argv) > 1 else m.group(1) == '3757')
        continue
    if inside:
        fr = re.search(r'(\d+)\. FrameLabel', ln)
        if fr:
            name = re.search(r'name: "([^"]+)"', ln)
            if name:
                print(f'frame {fr.group(1)}: {name.group(1)}')
