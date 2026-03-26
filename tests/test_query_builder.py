import pytest
from utils.query_builder import build_search_query, enhance_query, build_slot_query
from utils.slots import Slot

def test_build_search_query_basic() -> None:
    result = build_search_query("Light Attack Hit")
    assert "light" in result
    assert "attack" in result
    assert "hit" in result
    assert "+sword" in result

def test_build_search_query_no_special() -> None:
    result = build_search_query("Footsteps stone")
    assert "footsteps" in result
    assert "stone" in result
    assert "+sword" not in result

def test_build_search_query_level_up() -> None:
    result = build_search_query("Level Up")
    assert "+chime" in result

def test_build_search_query_crumble() -> None:
    result = build_search_query("Wall Crumble Secret")
    assert "+stone" in result
    assert "+break" in result

def test_enhance_query() -> None:
    result = enhance_query("test query")
    expected = "test query dark fantasy souls-like low reverb gritty armor medieval dark souls style"
    assert result == expected

def test_build_search_query_word_limit() -> None:
    result = build_search_query("This is a very long query with many words")
    assert result == "this +very +long +query"

def test_build_slot_query() -> None:
    slot: Slot = {
        'name': 'combat_light_attack_hit',
        'display_name': 'Light Attack Hit',
        'pos_tags': ['light', 'attack', 'hit'],
        'neg_tags': ['synth', 'beep'],
        'id': None
    }
    result = build_slot_query(slot)
    assert result == "light attack hit -synth -beep"
