"""Extract MapNodeExit_{Area} badges for the 9 major checkmark zones -> assets/icons/areas/."""
import io, sys, os, subprocess, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from PIL import Image

JAVA = r'_extractor\jre\jdk-21.0.12.1+1-jre\bin\java.exe'
FFDEC = r'_extractor\ffdec\ffdec-cli.jar'
SWF = r'game_assets\swfs\map.swf'
OUT = r'tools\_swf_tmp\mapnodes'
DEST = 'assets/icons/areas'
os.makedirs(OUT, exist_ok=True)
os.makedirs(DEST, exist_ok=True)

NODES = {
    'caves': 2290, 'boneyard': 2278, 'moon': 2242, 'core': 2254, 'jurassic': 2221,
    'theend': 2208, 'meatworld': 2273, 'dimensionx': 2237, 'endoftime': 2203,
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

for zone, tid in NODES.items():
    tmp = os.path.join(OUT, zone)
    os.makedirs(tmp, exist_ok=True)
    subprocess.run([JAVA, '-jar', FFDEC, '-format', 'sprite:png', '-ignorebackground', '-zoom', '1',
                    '-selectid', str(tid), '-select', f'{tid}:1', '-export', 'sprite', tmp, SWF],
                   capture_output=True, timeout=120)
    pngs = glob.glob(os.path.join(tmp, '**', '*.png'), recursive=True)
    if pngs:
        ok = norm(pngs[0], os.path.join(DEST, f'{zone}.png'))
        print(f'{zone:12s} {ok} ({os.path.getsize(pngs[0])}b)')
    else:
        print(f'{zone:12s} NO PNG')
