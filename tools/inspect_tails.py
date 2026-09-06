import sqlite3
import os
import struct
import lz4.block
from mewgenics_core import MewgenicsSaveManager

save_path = MewgenicsSaveManager.find_default_save()
mgr = MewgenicsSaveManager(save_path)

# Let's inspect tail_data across 10 different cats
print("Inspecting tail_data across cats:")
for k in [743, 747, 754, 758, 830, 831, 832, 833, 834, 835]:
    if k in mgr.cats:
        c = mgr.cats[k]
        print(f"\nCat #{k} '{c.name}': len(tail_data)={len(c.tail_data)}")
        print("  tail hex:", c.tail_data.hex())
