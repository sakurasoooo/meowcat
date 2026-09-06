import sqlite3
import os
import json

save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()

cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print(f"Total tables: {len(tables)}")
for name, sql in tables:
    cur.execute(f"SELECT COUNT(*) FROM `{name}`")
    cnt = cur.fetchone()[0]
    print(f"Table: {name} ({cnt} rows)")
    print(f"  SQL: {sql}\n")
