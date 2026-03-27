import pytest
from utils.query_builder import simple_query
from utils.slots import Slot

def test_simple_query_basic() -> None:
    slot: Slot = {
        'name': 'combat_light_attack_hit',
        'display_name': 'Light Attack Hit',
        'category': 'Combat',
        'fallbacks': ['sword hit', 'sword slash'],
        'id': None
    }
    result = simple_query(slot)
    assert result == "Light Attack Hit sword hit"

def test_simple_query_with_flavor() -> None:
    slot: Slot = {
        'name': 'combat_light_attack_hit',
        'display_name': 'Light Attack Hit',
        'category': 'Combat',
        'fallbacks': ['sword hit'],
        'id': None
    }
    result = simple_query(slot, "dark fantasy")
    assert result == "Light Attack Hit sword hit dark fantasy"
