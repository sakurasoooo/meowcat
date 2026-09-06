from mewgenics_core import MewgenicsSaveManager
mgr = MewgenicsSaveManager()

non_zero_mids = []
for k, c in mgr.cats.items():
    if any(b != 0 for b in c.mid_flags):
        non_zero_mids.append((k, c.name, c.mid_flags.hex()))

print(f"Cats with non-zero mid_flags: {len(non_zero_mids)} / {len(mgr.cats)}")
for k, name, h in non_zero_mids[:10]:
    print(f"  #{k} '{name}': {h}")