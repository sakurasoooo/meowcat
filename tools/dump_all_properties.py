import sqlite3, os
save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()
cur.execute("SELECT key, data FROM properties ORDER BY key")
for k, v in cur.fetchall():
    print(f"{k}: {repr(v)}")
