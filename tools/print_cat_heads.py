import sqlite3
import os

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT key, data FROM cats LIMIT 6")
for key, data in cur.fetchall():
    print(f"Cat {key}:")
    print(" ", data[:48].hex(' '))
