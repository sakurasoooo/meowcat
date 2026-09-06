from mewgenics_editor import MewgenicsSave

save = MewgenicsSave()
print(f"Total cats loaded: {len(save.cats)}")
print("Properties sample:")
for k in ['house_gold', 'house_food', 'current_day']:
    print(f"  {k}: {save.properties.get(k)}")

# Test Cat 835
c835 = save.cats[835]
print(f"\nCat 835 details:")
print(f"  Name: {c835.name}")
print(f"  Class: {c835.cat_class}")
print(f"  Voice: {c835.voice}")
print(f"  Base Stats: {c835.base_stats}")
print(f"  Abilities: Move={c835.move_ability}, Atk={c835.attack_ability}, Actives={c835.active_abilities}")
print(f"  Passives: {c835.passives}")

# Test creating a cat
new_c = save.create_cat(name="CelestialCat", gender="female", cat_class="Mage", stats={'str': 15, 'dex': 15, 'con': 15, 'int': 20, 'spd': 15, 'cha': 15, 'lck': 15})
print(f"\nNew Cat created:")
print(f"  ID: {new_c.key}, Name: {new_c.name}, Class: {new_c.cat_class}, Stats: {new_c.base_stats}")
