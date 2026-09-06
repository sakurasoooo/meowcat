"""Explicit alias: copy PascalCase-only passive icons to their UPPERCASE catalog key names."""
import io, sys, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DEST = 'assets/icons/passives'
files = {os.path.splitext(f)[0]: f for f in os.listdir(DEST) if f.endswith('.png')}

# 需要：上/下/帕斯卡变体映射（目录 key 多为全大写，SWF 图标文件名是帕斯卡/或其它）
MAP = {
    'FIGHTERSOUL': 'FightersSoul', 'HUNTERSOUL': 'HuntersSoul', 'MAGESOUL': 'MagesSoul',
    'CLERICSOUL': 'ClericsSoul', 'TANKSOUL': 'TanksSoul', 'THIEFSOUL': 'ThiefsSoul',
    'MONKSOUL': 'MonksSoul', 'BUTCHERSOUL': 'ButchersSoul', 'DRUIDSOUL': 'DruidsSoul',
    'TINKERERSOUL': 'TinkerersSoul', 'NECROMANCERSOUL': 'NecromancersSoul', 'PSYCHICSOUL': 'PsychicsSoul',
    'SOULBOND': 'SoulBound',
    'FIREASPECT': 'FireAspect', 'ICEASPECT': 'IceAspect', 'LIGHTNINGASPECT': 'LightningAspect',
    'UNSCARRED': 'Unscarred', 'HULKUP': 'HulkUp', 'FERVOR': 'Fervor', 'MERCILESS': 'Merciless',
    'NATUREGUIDANCE': 'NatureGuidance', 'LOVESONG': 'LoveSong', 'VERSATILEVOLCALIST': 'VersatileVolcalist',
    'SUPERFRIENDS': 'SuperFriends', 'SERVUSMORTEM': 'ServusMortem', 'LASTGRASP': 'LastGrasp',
    'STEALTHED': 'Stealthed', 'LONGSTRIDER': 'LongStrider', 'BULLSEYE': 'Bullseye',
    'FORCEFIELD': 'ForceField', 'DEATHCHILL': 'DeathChill', 'BRAINGEYSER': 'BrainGeyser',
}
done = 0
for key, src_name in MAP.items():
    fp = os.path.join(DEST, key + '.png')
    if os.path.exists(fp):
        continue
    src = files.get(src_name)
    if src:
        shutil.copyfile(os.path.join(DEST, src), os.path.join(DEST, key + '.png'))
        print(f'{key:22s} <- {src_name}')
        done += 1
    else:
        print(f'{key:22s} 无源文件 {src_name}')
print('done', done)
