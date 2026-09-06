import struct
from mewgenics_core import MewgenicsSaveManager

mgr = MewgenicsSaveManager()

for k in [743, 747, 754, 758, 830, 834, 835]:
    c = mgr.cats[k]
    t = c.tail_data
    # 0..4: u32
    u0 = struct.unpack_from('<I', t, 0)[0]
    # 4..12: double
    d0 = struct.unpack_from('<d', t, 4)[0]
    # 12..20: u64
    q0 = struct.unpack_from('<Q', t, 12)[0]
    # 20..28: u64
    q1 = struct.unpack_from('<q', t, 20)[0]
    
    # Let's inspect rest of bytes:
    rest = t[28:]
    non_zeros = [(i, b) for i, b in enumerate(rest) if b != 0]
    print(f"Cat #{k:3d} '{c.name}': u0={u0}, d0={d0:.4f}, q0={q0}, q1={q1}, non-zero rest: {non_zeros}")
