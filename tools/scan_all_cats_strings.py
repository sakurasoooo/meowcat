import sqlite3
import os

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats LIMIT 6")
rows = cur.fetchall()

def extract_strings(data):
    found = []
    # UTF-16LE
    i = 0
    while i < len(data) - 4:
        j = i
        chars = []
        while j < len(data) - 1:
            w = data[j:j+2]
            if w[1] == 0 and 32 <= w[0] <= 126:
                chars.append(chr(w[0]))
                j += 2
            else:
                break
        if len(chars) >= 3:
            found.append((i, "UTF16", ''.join(chars)))
            i = j
        else:
            i += 1
    # ASCII
    i = 0
    while i < len(data) - 3:
        j = i
        chars = []
        while j < len(data):
            b = data[j]
            if 32 <= b <= 126:
                chars.append(chr(b))
                j += 1
            else:
                break
        s = ''.join(chars)
        # Filter likely words
        if len(s) >= 3 and any(c.isalpha() for c in s):
            found.append((i, "ASCII", s))
            i = j
        else:
            i += 1
    return found

for key, data in rows:
    strs = extract_strings(data)
    print(f"\nCat {key} (length={len(data)}):")
    for off, enc, s in strs:
        # filter noise
        if any(w in s.lower() for w in ['none', 'male', 'female', 'step', 'melee', 'color', 'default', 'cat', 'fighter', 'mage', 'hunter', 'tank', 'healer', 'medic', 'rogue', 'thief', 'cleric']) or enc == "UTF16":
            print(f"  0x{off:04X}: [{enc}] {s}")
