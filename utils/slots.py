from typing import List, TypedDict, Optional

class Slot(TypedDict):
    name: str
    display_name: str
    category: str
    pos_tags: List[str]
    neg_tags: List[str]
    id: Optional[str]

def get_slots() -> List[Slot]:
    return [
        # Combat
        {"name": "combat_light_attack_hit", "display_name": "Light Attack Hit", "category": "Combat", "pos_tags": ["light", "attack", "hit", "sword", "slash", "melee"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": "817691"},
        {"name": "combat_heavy_attack_hit", "display_name": "Heavy Attack Hit", "category": "Combat", "pos_tags": ["heavy", "attack", "hit", "sword", "thud", "powerful"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "combat_parry_success", "display_name": "Parry Success", "category": "Combat", "pos_tags": ["parry", "success", "sword", "block", "metallic", "ring"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "combat_block_impact", "display_name": "Block Impact", "category": "Combat", "pos_tags": ["block", "impact", "shield", "clang", "armor", "metallic"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "combat_roll_dodge", "display_name": "Roll / Dodge", "category": "Combat", "pos_tags": ["roll", "dodge", "whoosh", "evade", "quick", "move"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "combat_stamina_break", "display_name": "Stamina Break", "category": "Combat", "pos_tags": ["stamina", "break", "exhaust", "grunt", "heavy", "breath"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "combat_enemy_hit", "display_name": "Enemy Hit", "category": "Combat", "pos_tags": ["enemy", "hit", "damage", "impact", "foe", "creature"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "combat_enemy_death", "display_name": "Enemy Death", "category": "Combat", "pos_tags": ["enemy", "death", "rattle", "monster", "creature", "fall"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "combat_player_death", "display_name": "Player Death", "category": "Combat", "pos_tags": ["player", "death", "gasp", "fall", "hero", "fatal"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "combat_healing", "display_name": "Healing", "category": "Combat", "pos_tags": ["healing", "health", "magic", "restore", "heal", "potion"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        # Movement
        {"name": "movement_footsteps_stone_metal", "display_name": "Footsteps (stone/metal)", "category": "Movement", "pos_tags": ["footsteps", "armor", "stone", "metal", "walk", "armored"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "movement_jump", "display_name": "Jump", "category": "Movement", "pos_tags": ["jump", "leap", "whoosh", "up", "bounding"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "movement_wall_hit_thud", "display_name": "Wall Hit / Thud", "category": "Movement", "pos_tags": ["wall", "hit", "thud", "impact", "collision", "slam"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "movement_wall_crumble_secret_reveal", "display_name": "Wall Crumble / Secret Reveal", "category": "Movement", "pos_tags": ["wall", "crumble", "secret", "stone", "collapse", "destruction"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "movement_ladder_climb", "display_name": "Ladder Climb", "category": "Movement", "pos_tags": ["ladder", "climb", "creak", "wooden", "ascend"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "movement_breakable_wall_break", "display_name": "Breakable Wall Break", "category": "Movement", "pos_tags": ["breakable", "wall", "break", "stone", "shatter", "destruction"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "movement_roll_through_gap", "display_name": "Roll Through Gap", "category": "Movement", "pos_tags": ["roll", "gap", "squeeze", "whoosh", "narrow", "passage"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "movement_chasm_wind_ambience", "display_name": "Chasm Wind Ambience", "category": "Movement", "pos_tags": ["chasm", "wind", "ambience", "abyss", "deep", "void"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        # UI
        {"name": "ui_menu_select_click", "display_name": "Menu Select / Click", "category": "UI", "pos_tags": ["menu", "select", "click", "ting", "ui", "press"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "ui_currency_pickup", "display_name": "Currency Pickup", "category": "UI", "pos_tags": ["currency", "pickup", "coin", "jingle", "gold", "treasure"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "ui_checkpoint_light", "display_name": "Checkpoint Light", "category": "UI", "pos_tags": ["checkpoint", "light", "fire", "bonfire", "ignite"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "ui_level_up", "display_name": "Level Up", "category": "UI", "pos_tags": ["level", "up", "chime", "upgrade", "character", "power"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "ui_low_stamina_warning", "display_name": "Low Stamina Warning", "category": "UI", "pos_tags": ["low", "stamina", "warning", "heartbeat", "breath", "alert"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
        {"name": "ui_death_screen", "display_name": "Death Screen", "category": "UI", "pos_tags": ["death", "screen", "drone", "ominous", "game", "over"], "neg_tags": ["synth", "beep", "electronic", "buzz", "sine"], "id": None},
    ]