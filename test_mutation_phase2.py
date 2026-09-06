import os
import sys
import json
import unittest
from PIL import Image

BASE_DIR = r"c:\Users\10107\Documents\github\meowcat"
sys.path.insert(0, BASE_DIR)
sys.stdout.reconfigure(encoding='utf-8')

from mutation_picker import make_tile, classify_mutation, get_mutation_icon_path, MutationPicker
from skill_card_widget import SkillCardWidget
from picker_dialog import UniversalGridPickerDialog
from mewgenics_core import CatRecord

class TestMutationTexturesAndDisorders(unittest.TestCase):

    def test_01_mutation_assets_count(self):
        """Verify that all 9 parts have extracted icons."""
        parts = ['head', 'ears', 'tail', 'body', 'legs', 'eyes', 'mouth', 'eyebrows', 'texture']
        for p in parts:
            pdir = os.path.join(BASE_DIR, "assets", "icons", "mutations", p)
            self.assertTrue(os.path.exists(pdir), f"Directory missing: {pdir}")
            files = [f for f in os.listdir(pdir) if f.endswith('.png')]
            self.assertGreater(len(files), 50, f"Part {p} has too few icons: {len(files)}")
            print(f"✓ Part [{p}] has {len(files)} valid icons")

    def test_02_make_tile_with_textures(self):
        """Verify make_tile composites textures cleanly."""
        # Head 300 (Square head)
        entry = {'id': 300, 'name': 'Square head', 'stats': {'con': 1}}
        tile = make_tile(entry, 'positive', size=72, slot_key='head')
        self.assertEqual(tile.size, (72, 72))
        self.assertEqual(tile.mode, 'RGBA')

        # Normal pure head (100)
        pure_entry = {'id': 100, 'name': '无突变', 'stats': {}}
        tile_pure = make_tile(pure_entry, 'normal', size=72, slot_key='head')
        self.assertEqual(tile_pure.size, (72, 72))

        # Missing part (-2)
        missing_entry = {'id': -2, 'name': '部位缺失', 'stats': {}}
        tile_missing = make_tile(missing_entry, 'missing', size=72, slot_key='head')
        self.assertEqual(tile_missing.size, (72, 72))
        print("✓ make_tile successfully handles mutation, pure base, and missing part")

    def test_03_disorders_catalog_and_icons(self):
        """Verify disorders_catalog.json and passive icons."""
        cat_path = os.path.join(BASE_DIR, "assets", "disorders_catalog.json")
        self.assertTrue(os.path.exists(cat_path), "disorders_catalog.json missing")
        with open(cat_path, 'r', encoding='utf-8') as f:
            disorders = json.load(f)
        self.assertEqual(len(disorders), 125, "Expected 125 disorders")

        rabies = next((d for d in disorders if d['key'] == 'Rabies'), None)
        self.assertIsNotNone(rabies, "Rabies not in disorders catalog")
        self.assertEqual(rabies['name'], '狂犬病')
        self.assertTrue(rabies['has_icon'])
        print(f"✓ disorders_catalog verified (sample: {rabies['key']} -> {rabies['name']})")

    def test_04_skill_card_widget_disorder_headless(self):
        """Test SkillCardWidget with catalog_type='disorder'."""
        import customtkinter as ctk
        root = ctk.CTk()
        root.withdraw()

        widget = SkillCardWidget(root, catalog_type="disorder", width=580, height=48)
        self.assertEqual(widget.get(), "None")

        widget.set("Rabies")
        self.assertEqual(widget.get(), "Rabies")
        self.assertEqual(widget.lbl_name.cget("text"), "狂犬病")
        self.assertIsNotNone(widget.lbl_icon.cget("image"))

        widget.set("None")
        self.assertEqual(widget.get(), "None")
        self.assertEqual(widget.lbl_name.cget("text"), "None (未选择)")

        root.destroy()
        print("✓ SkillCardWidget successfully supports catalog_type='disorder'")

if __name__ == '__main__':
    unittest.main()
