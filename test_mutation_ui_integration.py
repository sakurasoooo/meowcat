import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = r"c:\Users\10107\Documents\github\meowcat"
sys.path.insert(0, BASE_DIR)

from MewgenicsCatEditor import MewgenicsApp
from mewgenics_core import MewgenicsSaveManager, CatRecord
from mutation_picker import MutationPicker

def test_mutation_and_disorder_ui():
    print("=== Testing Mutation Real Textures & Disorder Slots in Editor UI ===")
    app = MewgenicsApp()
    app.withdraw()

    # Load save
    save_path = os.path.join(BASE_DIR, "verify_temp_save.sav.backup_20260906_162759")
    if not os.path.exists(save_path):
        save_path = os.path.join(r"C:\Users\10107\AppData\Roaming\Mewgenics", "76561198072124508", "savegame.sav")
    
    app.save_mgr = MewgenicsSaveManager(save_path)
    app.save_mgr.load()
    target_cat = list(app.save_mgr.cats.values())[0]
    app.select_cat(target_cat.key)

    cat = app.current_cat
    print(f"Loaded Cat: {cat.name} (Key: {cat.key})")

    # 1. Verify mutation slot buttons have valid icons
    head_btn = app.mutation_combos.get('head')
    assert head_btn is not None, "head mutation button missing"
    head_img = app._mutation_btn_image('head', cat.mutations.get('head', 100))
    assert head_img is not None, "head mutation button image missing"
    print("✓ Mutation UI Test 1: Cat head mutation button has valid CTkImage icon")

    # 2. Test Disorder SkillCardWidgets
    assert len(app.disorder_combos) == 2, "Expected 2 disorder combos"
    dis_0 = app.disorder_combos[0]
    dis_0.set('Rabies')
    assert dis_0.get() == 'Rabies', f"Expected Rabies, got {dis_0.get()}"
    assert dis_0.lbl_name.cget("text") == "狂犬病", f"Expected 狂犬病, got {dis_0.lbl_name.cget('text')}"
    print("✓ Disorder UI Test 2: Disorder card successfully set to Rabies (狂犬病)")

    # 3. Test cure all disorders
    app.on_cure_all_disorders()
    assert app.disorder_combos[0].get() == 'None'
    assert app.disorder_combos[1].get() == 'None'
    assert cat.disorders == ['None', 'None']
    print("✓ Disorder UI Test 3: Cure all disorders successfully reset both slots to None")

    # 4. Test apply synergistic disorders
    app.on_apply_synergistic_disorders()
    assert app.disorder_combos[0].get() != 'None'
    assert cat.disorders[0] != 'None'
    print(f"✓ Disorder UI Test 4: Synergistic disorders applied: {cat.disorders}")

    # 5. Test MutationPicker initialization & selection
    picked_id = None
    def mock_on_pick(mid):
        nonlocal picked_id
        picked_id = mid

    entries = app.game_data.get('mutations_detailed', {}).get('head', [])
    picker = MutationPicker(app, "选择突变 - 头部", entries, CatRecord.get_birth_defect_ids(),
                            current_id=100, norm_id=100, on_pick=mock_on_pick, slot_key='head')
    picker.withdraw()

    # Verify tile creation in picker
    tile_img = picker._tile(entries[0], 'positive', 56)
    assert tile_img is not None, "Picker tile creation failed"
    picker._pick(entries[0])
    assert picked_id == entries[0]['id'], f"Expected picked_id={entries[0]['id']}, got {picked_id}"
    print(f"✓ Mutation UI Test 5: MutationPicker successfully rendered tile and picked #{picked_id}")

    app.destroy()
    print("\n🎉 ALL MUTATION & DISORDER UI TESTS PASSED CLEANLY! 🎉")

if __name__ == '__main__':
    test_mutation_and_disorder_ui()
