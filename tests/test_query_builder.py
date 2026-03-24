import pytest
from utils.query_builder import build_search_query, enhance_query

def test_build_search_query_basic():
    result = build_search_query("Light Attack Hit")
    assert "light" in result
    assert "attack" in result
    assert "hit" in result
    assert "+sword" in result

def test_build_search_query_no_special():
    result = build_search_query("Footsteps stone")
    assert "footsteps" in result
    assert "stone" in result
    assert "+sword" not in result

def test_build_search_query_level_up():
    result = build_search_query("Level Up")
    assert "+chime" in result

def test_build_search_query_crumble():
    result = build_search_query("Wall Crumble Secret")
    assert "+stone" in result
    assert "+break" in result

def test_enhance_query():
    result = enhance_query("test query")
    expected = "test query dark fantasy souls-like low reverb gritty armor medieval dark souls style"
    assert result == expected