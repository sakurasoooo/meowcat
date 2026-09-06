from mewgenics_core import MewgenicsSaveManager

save_path = MewgenicsSaveManager.find_default_save()
mgr = MewgenicsSaveManager(save_path)

min_base = [999]*7
max_base = [-999]*7
min_bonus = [999]*7
max_bonus = [-999]*7

for c in mgr.cats.values():
    for i in range(7):
        min_base[i] = min(min_base[i], c.base_stats[i])
        max_base[i] = max(max_base[i], c.base_stats[i])
        min_bonus[i] = min(min_bonus[i], c.bonus_stats[i])
        max_bonus[i] = max(max_bonus[i], c.bonus_stats[i])

stat_names = ['STR', 'DEX', 'CON', 'INT', 'SPD', 'CHA', 'LCK']
print("Save file stats distribution across 675 cats:")
for i, name in enumerate(stat_names):
    print(f"  {name}: Base Range [{min_base[i]}, {max_base[i]}], Bonus Range [{min_bonus[i]}, {max_bonus[i]}]")
