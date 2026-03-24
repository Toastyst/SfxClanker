import pytest
import json
import os
from unittest.mock import patch, mock_open, ANY
from utils.cache import load_cache, save_cache, CacheEntry, get_sound_by_id

@patch('utils.cache.requests.get')
def test_get_sound_by_id_success(mock_get):
    mock_response = {
        'id': 123,
        'name': 'test sound',
        'previews': {'preview-hq-mp3': 'url'},
        'duration': 2.0,
        'num_downloads': 50
    }
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    result = get_sound_by_id('123', 'token')
    assert result == mock_response

@patch('utils.cache.requests.get')
def test_get_sound_by_id_failure(mock_get):
    mock_get.return_value.status_code = 404

    result = get_sound_by_id('123', 'token')
    assert result is None

@patch('utils.cache.os.path.exists')
@patch('builtins.open', new_callable=mock_open, read_data='{"filename": {"good_ids": ["1"], "last_updated": "2023-01-01"}}')
@patch('utils.cache.get_sound_by_id')
def test_load_cache_valid(mock_get_sound, mock_file, mock_exists):
    mock_exists.return_value = True
    mock_get_sound.return_value = {'duration': 2.0, 'num_downloads': 50, 'previews': {'preview-hq-mp3': 'url'}}

    cache = load_cache('token')
    assert 'filename' in cache
    assert cache['filename']['good_ids'] == ['1']

@patch('utils.cache.os.path.exists')
def test_load_cache_no_file(mock_exists):
    mock_exists.return_value = False

    cache = load_cache('token')
    assert cache == {}

@patch('utils.cache.json.dump')
def test_save_cache(mock_dump):
    cache = {'filename': {'good_ids': ['1', '2'], 'last_updated': '2023-01-01'}}
    save_cache(cache)

    mock_dump.assert_called_once_with(cache, ANY, indent=2)
