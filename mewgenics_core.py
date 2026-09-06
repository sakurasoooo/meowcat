import sqlite3
import os
import sys
import json
import struct
import lz4.block
import re
import shutil
import random
from datetime import datetime

_GAME_DATA_CACHE = None
def get_game_data_cache():
    global _GAME_DATA_CACHE
    if _GAME_DATA_CACHE is None:
        try:
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            p = os.path.join(base_dir, 'mewgenics_game_data.json')
            if not os.path.exists(p):
                p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mewgenics_game_data.json')
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    _GAME_DATA_CACHE = json.load(f)
            else:
                _GAME_DATA_CACHE = {}
        except Exception:
            _GAME_DATA_CACHE = {}
    return _GAME_DATA_CACHE

MUTATION_SLOTS = [
    ('body', '身体突变', 100 + 4, None),
    ('eyebrows', '眉毛突变', 280 + 4, 300 + 4),
    ('head', '头部突变', 120 + 4, None),
    ('ears', '耳部突变', 320 + 4, 340 + 4),
    ('tail', '尾部突变', 140 + 4, None),
    ('mouth', '嘴部突变', 360 + 4, None),
    ('legs', '腿部突变', 160 + 4, 180 + 4),
    ('texture', '毛皮突变', 80 + 12, None),
    ('arms', '手臂突变', 200 + 4, 220 + 4),
    ('eyes', '眼部突变', 240 + 4, 260 + 4)
]

class CatRecord:
    STAT_NAMES = ['str', 'dex', 'con', 'int', 'spd', 'cha', 'lck']

    def __init__(self, key, raw_data):
        self.key = key
        self.raw_data = bytearray(raw_data)
        self.is_modified = False
        self.parse()

    def parse(self):
        raw = self.raw_data
        self.version = struct.unpack_from('<I', raw, 0)[0]
        self.guid = struct.unpack_from('<Q', raw, 4)[0]
        
        # Name
        self.name_len = struct.unpack_from('<Q', raw, 0x0c)[0]
        self.name = raw[0x14 : 0x14 + self.name_len * 2].decode('utf-16le', errors='ignore')
        
        # Find voice & stats
        m = re.search(rb'(?:male\d+|female\d+|robotom|spidercat|demoncat|robotcat)', raw)
        if not m:
            raise ValueError(f"Could not locate voice string in cat {self.key}")
            
        p_voice = m.start()
        self.p_voice_len = p_voice - 8
        self.voice_len = struct.unpack_from('<Q', raw, self.p_voice_len)[0]
        self.voice = raw[p_voice : p_voice + self.voice_len].decode('ascii', errors='ignore')
        
        # Everything before voice is the pre_voice_chunk (header, name, title, 368-byte parts)
        # Note: name is at 0x14..0x14+name_len*2
        self.p_name_end = 0x14 + self.name_len * 2
        self.pre_voice_body = bytearray(raw[self.p_name_end : self.p_voice_len])
        
        # Parse title & parts_chunk
        self.title_len = struct.unpack_from('<Q', self.pre_voice_body, 0)[0]
        self.title = self.pre_voice_body[8 : 8 + self.title_len].decode('ascii', errors='ignore')
        self.p_parts = 8 + self.title_len + 4
        self.parts_chunk = bytearray(self.pre_voice_body[self.p_parts:])

        # Parse 10 mutation slots (Dominant & Recessive alleles)
        self.mutations = {}
        self.recessive_mutations = {}
        for slot_key, slot_cn, off1, off2 in MUTATION_SLOTS:
            if off1 + 4 <= len(self.parts_chunk):
                m_id = struct.unpack_from('<i', self.parts_chunk, off1)[0]
                self.mutations[slot_key] = m_id
            else:
                self.mutations[slot_key] = 0

            if off2 and off2 + 4 <= len(self.parts_chunk):
                r_id = struct.unpack_from('<i', self.parts_chunk, off2)[0]
                self.recessive_mutations[slot_key] = r_id
            else:
                self.recessive_mutations[slot_key] = None
        
        # Voice pitch
        p = p_voice + self.voice_len
        self.pitch = struct.unpack_from('<d', raw, p)[0]; p += 8
        
        # Base stats & bonus stats
        self.base_stats = list(struct.unpack_from('<7i', raw, p)); p += 28
        self.bonus_stats = list(struct.unpack_from('<7i', raw, p)); p += 28
        
        # Scan remaining strings
        p_search = p
        strings = []
        while p_search < len(raw) - 8:
            slen = struct.unpack_from('<Q', raw, p_search)[0]
            if 1 <= slen <= 50 and p_search + 8 + slen <= len(raw):
                chunk = raw[p_search + 8 : p_search + 8 + slen]
                if all(32 <= b <= 126 for b in chunk) and any(chr(b).isalpha() for b in chunk):
                    s = chunk.decode('ascii')
                    strings.append((p_search, slen, s))
                    p_search += 8 + slen
                    continue
            p_search += 1
            
        self.str_records = strings
        str_vals = [s[2] for s in strings]
        
        self.boon = str_vals[0] if len(str_vals) > 0 else 'none'
        self.move_ability = str_vals[1] if len(str_vals) > 1 else 'DefaultMove'
        self.attack_ability = str_vals[2] if len(str_vals) > 2 else 'BasicMelee'
        
        # Active abilities (up to 4)
        self.active_abilities = []
        for i in range(3, min(7, len(str_vals))):
            self.active_abilities.append(str_vals[i])
        while len(self.active_abilities) < 4:
            self.active_abilities.append('None')
            
        # Passives (up to 8)
        self.passives = []
        for i in range(7, min(15, len(str_vals))):
            self.passives.append(str_vals[i])
        while len(self.passives) < 8:
            self.passives.append('None')
            
        # Class (usually the last string or 15th)
        self.cat_class = str_vals[-1] if len(str_vals) >= 16 else 'Colorless'
        
        # Save fixed byte segments between strings
        self.mid_flags = raw[p : self.str_records[0][0]] if self.str_records else raw[p:p+28]
        p_post_boon = self.str_records[0][0] + 8 + self.str_records[0][1]
        self.post_boon_flags = raw[p_post_boon : self.str_records[1][0]] if len(self.str_records) > 1 else b''
        
        # Post class tail & Sexuality
        last_str_end = self.str_records[-1][0] + 8 + self.str_records[-1][1]
        self.tail_data = bytearray(raw[last_str_end:])
        
        # Sexuality decoding from tail_data
        if len(self.tail_data) >= 12:
            self.sexuality_val = struct.unpack_from('<d', self.tail_data, 4)[0]
        else:
            self.sexuality_val = 0.0
            
        if self.sexuality_val <= 0.05:
            self.sexuality = "Straight (异性恋)"
        elif self.sexuality_val < 0.33:
            self.sexuality = "Bisexual (双性恋)"
        else:
            self.sexuality = "Gay (同性恋)"

        self.libido = "Mid (正常)"
        self.aggression = "Mid (适中)"
        self.inbred_level = 0

    @property
    def mutation_stat_modifiers(self):
        mods = {k: 0 for k in self.STAT_NAMES}
        gd = get_game_data_cache()
        mut_detailed = gd.get('mutations_detailed', {})
        for slot_key, mid in self.mutations.items():
            if mid >= 300:
                entries = mut_detailed.get(slot_key, [])
                for e in entries:
                    if e.get('id') == mid:
                        for sk, sv in e.get('stats', {}).items():
                            if sk in mods:
                                mods[sk] += sv
                        break
        return mods

    @property
    def effective_stats(self):
        mut_mods = self.mutation_stat_modifiers
        return [b + mut_mods[k] + bon for k, b, bon in zip(self.STAT_NAMES, self.base_stats, self.bonus_stats)]

    @property
    def total_stats(self):
        return self.effective_stats

    def set_mutation(self, slot_key, mutation_id, sync_recessive=False):
        self.mutations[slot_key] = mutation_id
        for sk, scn, off1, off2 in MUTATION_SLOTS:
            if sk == slot_key:
                if off1 + 4 <= len(self.parts_chunk):
                    struct.pack_into('<i', self.parts_chunk, off1, mutation_id)
                if sync_recessive and off2 and off2 + 4 <= len(self.parts_chunk):
                    struct.pack_into('<i', self.parts_chunk, off2, mutation_id)
                    self.recessive_mutations[slot_key] = mutation_id
                break
        self.pre_voice_body[self.p_parts : self.p_parts + len(self.parts_chunk)] = self.parts_chunk
        self.is_modified = True

    def set_recessive_mutation(self, slot_key, mutation_id):
        self.recessive_mutations[slot_key] = mutation_id
        for sk, scn, off1, off2 in MUTATION_SLOTS:
            if sk == slot_key:
                if off2 and off2 + 4 <= len(self.parts_chunk):
                    struct.pack_into('<i', self.parts_chunk, off2, mutation_id)
                break
        self.pre_voice_body[self.p_parts : self.p_parts + len(self.parts_chunk)] = self.parts_chunk
        self.is_modified = True

    def clear_all_mutations(self):
        default_normal_ids = {
            'texture': 246,
            'body': 100,
            'head': 100,
            'tail': 100,
            'legs': 100,
            'arms': 100,
            'eyes': 100,
            'eyebrows': 100,
            'ears': 100,
            'mouth': 100
        }
        for sk, norm_id in default_normal_ids.items():
            self.set_mutation(sk, norm_id, sync_recessive=True)

    def apply_god_mutations(self):
        god_preset = {
            'texture': 306,
            'body': 304,
            'head': 309,
            'tail': 324,
            'legs': 322,
            'arms': 322,
            'eyes': 303,
            'eyebrows': 304,
            'ears': 300,
            'mouth': 751
        }
        for sk, mid in god_preset.items():
            self.set_mutation(sk, mid, sync_recessive=True)

    def build_bytes(self):
        buf = bytearray()
        buf.extend(struct.pack('<I', self.version))
        buf.extend(struct.pack('<Q', self.guid))
        
        # Name
        name_enc = self.name.encode('utf-16le')
        buf.extend(struct.pack('<Q', len(self.name)))
        buf.extend(name_enc)
        
        # Pre-voice body (title & appearance parts)
        buf.extend(self.pre_voice_body)
        
        # Voice
        voice_enc = self.voice.encode('ascii')
        buf.extend(struct.pack('<Q', len(voice_enc)))
        buf.extend(voice_enc)
        
        # Pitch
        buf.extend(struct.pack('<d', self.pitch))
        
        # Base stats & bonus stats
        buf.extend(struct.pack('<7i', *self.base_stats))
        buf.extend(struct.pack('<7i', *self.bonus_stats))
        
        # Mid flags
        buf.extend(self.mid_flags)
        
        # Boon
        boon_enc = self.boon.encode('ascii')
        buf.extend(struct.pack('<Q', len(boon_enc)))
        buf.extend(boon_enc)
        
        # Post boon flags
        buf.extend(self.post_boon_flags)
        
        # Move ability
        move_enc = self.move_ability.encode('ascii')
        buf.extend(struct.pack('<Q', len(move_enc)))
        buf.extend(move_enc)
        
        # Attack ability
        atk_enc = self.attack_ability.encode('ascii')
        buf.extend(struct.pack('<Q', len(atk_enc)))
        buf.extend(atk_enc)
        
        # 4 Actives
        for act in self.active_abilities[:4]:
            act_enc = act.encode('ascii')
            buf.extend(struct.pack('<Q', len(act_enc)))
            buf.extend(act_enc)
            
        # Passives
        for pas in self.passives[:4]:
            pas_enc = pas.encode('ascii')
            buf.extend(struct.pack('<Q', len(pas_enc)))
            buf.extend(pas_enc)
            
        # Extra passives (with 4-byte rank ints)
        for pas in self.passives[4:8]:
            pas_enc = pas.encode('ascii')
            buf.extend(struct.pack('<Q', len(pas_enc)))
            buf.extend(pas_enc)
            buf.extend(struct.pack('<i', 1)) # rank 1
            
        # Pre-class flags
        buf.extend(b'\x05\x00\x00\x00\x00\x05\x00\x00\x00\x00\x05\x00\x00\x00\x00\x05\x00\x00\x00\x00')
        
        # Class
        cls_enc = self.cat_class.encode('ascii')
        buf.extend(struct.pack('<Q', len(cls_enc)))
        buf.extend(cls_enc)
        
        # Update sexuality in tail_data
        if len(self.tail_data) >= 12:
            if "Straight" in self.sexuality:
                s_val = 0.0
            elif "Bisexual" in self.sexuality:
                s_val = 0.25
            else:
                s_val = 0.45
            struct.pack_into('<d', self.tail_data, 4, s_val)

        # Tail
        buf.extend(self.tail_data)
        return bytes(buf)

class MewgenicsSaveManager:
    @classmethod
    def find_default_save(cls):
        base_dir = os.path.expandvars(r"%APPDATA%\Glaiel Games\Mewgenics")
        target_name = "steamcampaign01.sav"
        p1 = os.path.join(base_dir, "76561198096981781", "saves", target_name)
        if os.path.exists(p1):
            return p1
        if os.path.exists(base_dir):
            for root, dirs, files in os.walk(base_dir):
                if target_name in files:
                    return os.path.join(root, target_name)
        return p1

    def __init__(self, file_path=None):
        self.file_path = file_path or self.find_default_save()
        self.cats = {}
        self.properties = {}
        if self.file_path and os.path.exists(self.file_path):
            self.load()

    def load(self, path=None):
        if path:
            self.file_path = path
        conn = sqlite3.connect(self.file_path)
        cur = conn.cursor()
        
        cur.execute("SELECT key, data FROM properties")
        self.properties = {k: v for k, v in cur.fetchall()}
        
        cur.execute("SELECT key, data FROM cats")
        self.cats = {}
        for k, blob in cur.fetchall():
            unc_sz = struct.unpack_from('<I', blob, 0)[0]
            raw = lz4.block.decompress(blob[4:], uncompressed_size=unc_sz)
            try:
                c = CatRecord(k, raw)
                c.is_in_house = False
                c.house_room = ""
                self.cats[k] = c
            except Exception as e:
                pass

        # Parse living cats from house_state
        self.house_cat_ids = set()
        self.house_cat_rooms = {}
        self.house_state_raw = None
        try:
            cur.execute("SELECT data FROM files WHERE key='house_state'")
            row = cur.fetchone()
            if row and row[0]:
                self.house_state_raw = bytearray(row[0])
                data = self.house_state_raw
                p = 0
                while p < len(data) - 8:
                    slen = struct.unpack_from('<Q', data, p)[0]
                    if 1 <= slen <= 50 and p + 8 + slen <= len(data):
                        chunk = data[p+8 : p+8+slen]
                        if all(32 <= b <= 126 for b in chunk):
                            s = chunk.decode('ascii')
                            cat_id_pos = p - 8
                            if cat_id_pos >= 0:
                                cid = struct.unpack_from('<Q', data, cat_id_pos)[0]
                                if cid in self.cats:
                                    self.house_cat_ids.add(cid)
                                    self.house_cat_rooms[cid] = s
                                    self.cats[cid].is_in_house = True
                                    self.cats[cid].house_room = s
                            p += 8 + slen
                            continue
                    p += 1
        except Exception as e:
            pass

        conn.close()
        return len(self.cats)

    def set_cat_room(self, cat_key, room_name):
        cat = self.cats.get(cat_key)
        if not cat:
            return False
            
        old_room = getattr(cat, 'house_room', '')
        if old_room == room_name:
            return True
            
        valid_rooms = ['Floor1_Large', 'Floor1_Small', 'Attic']
        
        # If moving out of house (or "移出家园")
        if not room_name or room_name not in valid_rooms or "移出" in room_name:
            self._remove_from_house_state(cat_key)
            cat.is_in_house = False
            cat.house_room = ""
            if cat_key in self.house_cat_ids:
                self.house_cat_ids.remove(cat_key)
            if cat_key in self.house_cat_rooms:
                del self.house_cat_rooms[cat_key]
            return True

        # Moving to a valid house room
        cat.is_in_house = True
        cat.house_room = room_name
        self.house_cat_ids.add(cat_key)
        self.house_cat_rooms[cat_key] = room_name
        
        updated = self._update_room_in_house_state(cat_key, room_name)
        if not updated:
            self._append_to_house_state(cat_key, room_name)
        return True

    def _update_room_in_house_state(self, cat_key, new_room):
        if not getattr(self, 'house_state_raw', None):
            return False
        raw = self.house_state_raw
        p = 0
        while p < len(raw) - 8:
            slen = struct.unpack_from('<Q', raw, p)[0]
            if slen in [5, 12] and p + 8 + slen <= len(raw):
                s = raw[p+8 : p+8+slen].decode('ascii', errors='ignore')
                if s in ['Floor1_Large', 'Floor1_Small', 'Attic']:
                    cid_pos = p - 8
                    cid = struct.unpack_from('<Q', raw, cid_pos)[0]
                    if cid == cat_key:
                        old_bytes = struct.pack('<Q', slen) + s.encode('ascii')
                        new_bytes = struct.pack('<Q', len(new_room)) + new_room.encode('ascii')
                        raw[p : p + len(old_bytes)] = new_bytes
                        return True
                    p += 8 + slen + 32
                    continue
            p += 1
        return False

    def _append_to_house_state(self, cat_key, room_name):
        if not getattr(self, 'house_state_raw', None):
            return False
        raw = self.house_state_raw
        val0, count = struct.unpack_from('<II', raw, 0)
        struct.pack_into('<I', raw, 4, count + 1)
        entry = bytearray()
        entry.extend(struct.pack('<Q', cat_key))
        entry.extend(struct.pack('<Q', len(room_name)))
        entry.extend(room_name.encode('ascii'))
        entry.extend(struct.pack('<4d', 15.0, 1.0, 0.0, 0.0))
        raw.extend(entry)
        return True

    def _remove_from_house_state(self, cat_key):
        if not getattr(self, 'house_state_raw', None):
            return False
        raw = self.house_state_raw
        p = 0
        while p < len(raw) - 8:
            slen = struct.unpack_from('<Q', raw, p)[0]
            if slen in [5, 12] and p + 8 + slen <= len(raw):
                s = raw[p+8 : p+8+slen].decode('ascii', errors='ignore')
                if s in ['Floor1_Large', 'Floor1_Small', 'Attic']:
                    cid_pos = p - 8
                    cid = struct.unpack_from('<Q', raw, cid_pos)[0]
                    if cid == cat_key:
                        entry_end = p + 8 + slen + 32
                        del raw[cid_pos : entry_end]
                        val0, count = struct.unpack_from('<II', raw, 0)
                        struct.pack_into('<I', raw, 4, max(0, count - 1))
                        return True
                    p += 8 + slen + 32
                    continue
            p += 1
        return False

    def backup(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.file_path}.backup_{ts}"
        shutil.copy2(self.file_path, backup_path)
        return backup_path

    def save(self, target_path=None):
        if target_path and target_path != self.file_path:
            shutil.copy2(self.file_path, target_path)
            dest = target_path
            backup_result = target_path
        else:
            backup_result = self.backup()
            dest = self.file_path
        
        conn = sqlite3.connect(dest)
        cur = conn.cursor()
        
        # Save properties
        for k, v in self.properties.items():
            cur.execute("INSERT OR REPLACE INTO properties (key, data) VALUES (?, ?)", (k, v))
            
        # Save cats
        for key, cat in self.cats.items():
            raw_cat = cat.build_bytes()
            comp = lz4.block.compress(raw_cat, store_size=False)
            blob = struct.pack('<I', len(raw_cat)) + comp
            cur.execute("INSERT OR REPLACE INTO cats (key, data) VALUES (?, ?)", (key, blob))
            
        # Save house_state if present
        if getattr(self, 'house_state_raw', None):
            cur.execute("INSERT OR REPLACE INTO files (key, data) VALUES (?, ?)", ('house_state', bytes(self.house_state_raw)))

        conn.commit()
        conn.close()
        return backup_result

    def create_new_cat(self, name="NewCat", gender="male", cat_class="Colorless", stats=None, template_id=835, room="Floor1_Large", sexuality="Straight (异性恋)"):
        if template_id not in self.cats:
            template_id = max(self.cats.keys()) if self.cats else 1
            
        template = self.cats[template_id]
        new_key = max(self.cats.keys()) + 1 if self.cats else 1
        
        # Clone template bytes
        raw_clone = bytearray(template.build_bytes())
        new_cat = CatRecord(new_key, raw_clone)
        new_cat.name = name
        new_cat.guid = random.getrandbits(64)
        new_cat.cat_class = cat_class
        new_cat.voice = "male55" if gender == "male" else "female50"
        new_cat.sexuality = sexuality
        
        if stats:
            for i, k in enumerate(CatRecord.STAT_NAMES):
                if k in stats:
                    new_cat.base_stats[i] = int(stats[k])
                    
        self.cats[new_key] = new_cat
        if room and room != "移出家园 (谱系)":
            self.set_cat_room(new_key, room)
        return new_cat
