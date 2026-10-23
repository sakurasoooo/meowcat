"""Extract ui.swf sprite 101 UnlockArea badges (label_frame+1 = FFDec frame)."""
import io, sys, os, subprocess, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from PIL import Image

JAVA = r'_extractor\jre\jdk-21.0.12.1+1-jre\bin\java.exe'
FFDEC = r'_extractor\ffdec\ffdec-cli.jar'
SWF = r'game_assets\swfs\ui.swf'
OUT = r'tools\_swf_tmp\unlockbadges'
DEST = 'assets/icons/areas'
os.makedirs(OUT, exist_ok=True)
os.makedirs(DEST, exist_ok=True)

# zone -> label_frame (sprite 101)
Z = {'caves': 25, 'boneyard': 26, 'core': 29, 'moon': 31, 'jurassic': 34, 'theend': 36,
     'meatworld': 37, 'dimensionx': 38, 'endoftime': 39}

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

for zone, lf in Z.items():
    ff = lf + 1  # SWF/FFDec 帧 = 标签帧 + 1
    tmp = os.path.join(OUT, zone)
    os.makedirs(tmp, exist_ok=True)
    subprocess.run([JAVA, '-jar', FFDEC, '-format', 'sprite:png', '-ignorebackground', '-zoom', '1',
                    '-selectid', '101', '-select', f'101:{ff}', '-export', 'sprite', tmp, SWF],
                   capture_output=True, timeout=120)
    pngs = glob.glob(os.path.join(tmp, '**', '*.png'), recursive=True)
    if pngs:
        ok = norm(pngs[0], os.path.join(DEST, f'{zone}.png'))
        print(f'{zone:12s} label帧{lf}→FF{ff}: {"OK" if ok else "EMPTY"} ({os.path.getsize(pngs[0])}b)')
    else:
        print(f'{zone:12s} NO PNG')
