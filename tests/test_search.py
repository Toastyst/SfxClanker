import pytest
from unittest.mock import patch, MagicMock
from utils.search import simple_search_slot
from utils.slots import Slot

@patch('utils.search.weighted_search_freesound')
def test_simple_search_slot(mock_weighted_search):
    mock_weighted_search.return_value = ([
        {'id': '1', 'name': 'test1', 'duration': 1.0, 'num_downloads': 100, 'previews': {'preview-lq-mp3': 'url1'}, 'analysis': {}},
        {'id': '2', 'name': 'test2', 'duration': 2.0, 'num_downloads': 200, 'previews': {'preview-lq-mp3': 'url2'}, 'analysis': {}}
    ], True)

    slot: Slot = {
        'name': 'combat_light_attack_hit',
        'display_name': 'Light Attack Hit',
        'category': 'Combat',
        'fallbacks': ['sword hit', 'sword slash'],
        'id': None
    }

    result = simple_search_slot(slot, "", False, ['key'])

    assert len(result) == 2
    assert result[0]['id'] == '2'  # higher score first (200 dl >100)
    assert 'quality_score' in result[0]
    mock_weighted_search.assert_called_once()
