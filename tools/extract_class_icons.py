"""Extract 14 class FontIcons from ui.swf -> assets/icons/classes/<Class>.png (normalized)."""
import io as _io, sys as _sys, os, subprocess, glob, shutil
_sys.stdout = _io.TextIOWrapper(_sys.stdout.buffer, encoding='utf-8')
from PIL import Image, ImageOps

JAVA = r'_extractor\jre\jdk-21.0.12.1+1-jre\bin\java.exe'
FFDEC = r'_extractor\ffdec\ffdec-cli.jar'
SWF = r'game_assets\swfs\ui.swf'
OUT = r'tools\_swf_tmp\class'
DEST = r'assets\icons\classes'
os.makedirs(OUT, exist_ok=True)
os.makedirs(DEST, exist_ok=True)

CLASSES = {
    'Fighter': 2659, 'Mage': 2657, 'Hunter': 2655, 'Tank': 2653, 'Thief': 2651,
    'Medic': 2649, 'Necromancer': 2647, 'Psychic': 2645, 'Druid': 2643,
    'Tinkerer': 2641, 'Monk': 2639, 'Butcher': 2637, 'Jester': 2635, 'Colorless': 2633,
}

def norm(src, dest, target=64, pad=4):
    img = Image.open(src).convert('RGBA')
    bbox = img.getbbox()
    if not bbox:
        return False
    img = img.crop(bbox)
    inner = target - pad * 2
    s = min(inner / img.width, inner / img.height)
    img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
    canvas = Image.new('RGBA', (target, target), (0, 0, 0, 0))
    canvas.paste(img, ((target - img.width) // 2, (target - img.height) // 2), img)
    canvas.save(dest, 'PNG', optimize=True)
    return True

for name, chid in CLASSES.items():
    tmp = os.path.join(OUT, f'{name}')
    os.makedirs(tmp, exist_ok=True)
    subprocess.run([JAVA, '-jar', FFDEC, '-format', 'sprite:png', '-ignorebackground', '-zoom', '1',
                    '-selectid', str(chid), '-select', f'{chid}:1', '-export', 'sprite', tmp, SWF],
                   capture_output=True, timeout=120)
    pngs = glob.glob(os.path.join(tmp, '**', '*.png'), recursive=True)
    if pngs:
        ok = norm(pngs[0], os.path.join(DEST, f'{name}.png'))
        print(f'{name}: {"OK" if ok else "EMPTY"} ({os.path.getsize(pngs[0])}b)')
    else:
        print(f'{name}: NO PNG exported')
