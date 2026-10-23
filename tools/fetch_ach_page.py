"""Fetch wiki achievements page, extract image refs."""
import io, sys, re, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
r = subprocess.run(['powershell', '-Command',
                    "(Invoke-WebRequest -UseBasicParsing 'https://mewcodex.github.io/achievements.html?lang=en' -TimeoutSec 30).Content"],
                   capture_output=True, text=True)
t = r.stdout
print('len', len(t))
imgs = sorted(set(re.findall(r'[\w./-]+\.(?:png|webp|jpg)', t)))
print('img refs:', imgs[:25])
# icon url patterns
pat = sorted(set(re.findall(r'(?:AbilityIcon|AchievementIcon|PassiveIcon|res/[A-Za-z]+/)[A-Za-z0-9._/-]*', t)))
print('icon patterns:', pat[:25])
# achievement data keys
ak = sorted(set(re.findall(r'"?\b(?:achievement_)?(?:icon|image|frame|sprite)[A-Za-z_]*"?\s*:', t)))
print('icon keys:', ak[:20])
