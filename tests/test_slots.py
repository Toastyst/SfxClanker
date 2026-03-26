import pytest
from utils.slots import get_slots

def test_get_slots():
    slots = get_slots()
    assert len(slots) == 24
    for slot in slots:
        assert 'name' in slot
        assert 'display_name' in slot
        assert 'pos_tags' in slot
        assert 'neg_tags' in slot
        assert isinstance(slot['pos_tags'], list)
        assert isinstance(slot['neg_tags'], list)
        assert len(slot['pos_tags']) >= 3
        assert len(slot['neg_tags']) >= 3
        assert slot['name'].startswith(('combat_', 'movement_', 'ui_'))
        assert 'id' in slot  # optional