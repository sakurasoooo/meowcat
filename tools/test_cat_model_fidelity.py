import sqlite3
import os
import struct
import lz4.block
import re

class CatModel:
    def __init__(self, key, raw_data):
        self.key = key
        self.raw_data = raw_data
        self.parse(raw_data)
        
    def parse(self, data):
        self.version = struct.unpack_from('<I', data, 0)[0]
        self.guid = struct.unpack_from('<Q', data, 4)[0]
        self.name_len = struct.unpack_from('<Q', data, 0x0C)[0]
        self.name = data[0x14 : 0x14 + self.name_len * 2].decode('utf-16le')
        
        pos = 0x14 + self.name_len * 2
        # Title prefix is 24 bytes + string
        self.pre_title = data[pos : pos + 24]
        pos += 24
        self.title_len = struct.unpack_from('<Q', data, pos)[0]
        pos += 8
        self.title = data[pos : pos + self.title_len].decode('ascii', errors='ignore')
        pos += self.title_len
        
        # Next 4 bytes is uint32 (usually 1)
        self.post_title_u32 = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        
        # Parts chunk is 368 bytes!
        self.parts_chunk = bytearray(data[pos : pos + 368])
        pos += 368
        
        # Voice string
        self.voice_len = struct.unpack_from('<Q', data, pos)[0]
        pos += 8
        self.voice = data[pos : pos + self.voice_len].decode('ascii', errors='ignore')
        pos += self.voice_len
        
        # Voice pitch (double)
        self.pitch = struct.unpack_from('<d', data, pos)[0]
        pos += 8
        
        # 7 Base stats
        self.base_stats = list(struct.unpack_from('<7i', data, pos))
        pos += 28
        
        # 7 Bonus stats
        self.bonus_stats = list(struct.unpack_from('<7i', data, pos))
        pos += 28
        
        # After bonus stats, there is a fixed 28-byte int/flag chunk
        self.mid_stats_flags = data[pos : pos + 28]
        pos += 28
        
        # Now 16 strings:
        # 0: boon
        # 1: move_ability
        # 2: attack_ability
        # 3..6: active_spells (4)
        # 7..14: passives (8)
        # 15: class
        self.strings = []
        for i in range(16):
            slen = struct.unpack_from('<Q', data, pos)[0]
            pos += 8
            sval = data[pos : pos + slen].decode('ascii', errors='ignore')
            pos += slen
            self.strings.append(sval)
            
        # Any trailing data (level, exp, etc.)
        self.trailing_data = data[pos:]

    def serialize(self):
        buf = bytearray()
        buf.extend(struct.pack('<I', self.version))
        buf.extend(struct.pack('<Q', self.guid))
        
        # Name (UTF-16LE)
        name_bytes = self.name.encode('utf-16le')
        buf.extend(struct.pack('<Q', len(self.name)))
        buf.extend(name_bytes)
        
        # Pre-title
        buf.extend(self.pre_title)
        
        # Title
        title_bytes = self.title.encode('ascii')
        buf.extend(struct.pack('<Q', len(title_bytes)))
        buf.extend(title_bytes)
        
        # Post-title u32
        buf.extend(struct.pack('<I', self.post_title_u32))
        
        # Parts chunk
        buf.extend(self.parts_chunk)
        
        # Voice
        voice_bytes = self.voice.encode('ascii')
        buf.extend(struct.pack('<Q', len(voice_bytes)))
        buf.extend(voice_bytes)
        
        # Pitch
        buf.extend(struct.pack('<d', self.pitch))
        
        # Base stats
        buf.extend(struct.pack('<7i', *self.base_stats))
        
        # Bonus stats
        buf.extend(struct.pack('<7i', *self.bonus_stats))
        
        # Mid stats flags
        buf.extend(self.mid_stats_flags)
        
        # 16 strings
        for s in self.strings:
            s_bytes = s.encode('ascii')
            buf.extend(struct.pack('<Q', len(s_bytes)))
            buf.extend(s_bytes)
            
        # Trailing
        buf.extend(self.trailing_data)
        return bytes(buf)

# Test against all 675 cats!
save_path = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics\76561198096981781\saves\steamcampaign01.sav")
conn = sqlite3.connect(save_path)
cur = conn.cursor()
cur.execute("SELECT key, data FROM cats")
all_cats = cur.fetchall()

success_count = 0
failed_count = 0
errors = []

for key, blob in all_cats:
    unc_sz = struct.unpack_from('<I', blob, 0)[0]
    raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
    try:
        model = CatModel(key, raw)
        reserialized = model.serialize()
        if reserialized == raw:
            success_count += 1
        else:
            failed_count += 1
            errors.append((key, f"Size diff: orig {len(raw)} vs reser {len(reserialized)}"))
    except Exception as e:
        failed_count += 1
        errors.append((key, str(e)))

print(f"Tested {len(all_cats)} cats:")
print(f"  SUCCESS (100% byte-for-byte exact): {success_count}")
print(f"  FAILED: {failed_count}")
if errors:
    print(f"  Sample errors: {errors[:5]}")
