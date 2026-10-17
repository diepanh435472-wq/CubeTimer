"""Tests for puzzle specifications."""
import pytest
from cubetimer.core.puzzles import get_puzzle, PUZZLES


def test_puzzles_dictionary_complete():
    """Test that all expected puzzles are defined."""
    expected_keys = ["222", "333", "444", "555", "666", "777"]
    assert set(PUZZLES.keys()) == set(expected_keys)


def test_puzzle_specs():
    """Test that puzzle specs have correct attributes."""
    assert PUZZLES["222"].size == 2
    assert PUZZLES["222"].length == 11
    assert PUZZLES["222"].name == "2x2x2"
    
    assert PUZZLES["333"].size == 3
    assert PUZZLES["333"].length == 20
    assert PUZZLES["333"].name == "3x3x3"
    
    assert PUZZLES["444"].size == 4
    assert PUZZLES["444"].length == 40
    
    assert PUZZLES["555"].size == 5
    assert PUZZLES["555"].length == 60
    
    assert PUZZLES["666"].size == 6
    assert PUZZLES["666"].length == 80
    
    assert PUZZLES["777"].size == 7
    assert PUZZLES["777"].length == 100


def test_get_puzzle_valid():
    """Test get_puzzle with valid keys."""
    puzzle = get_puzzle("333")
    assert puzzle.key == "333"
    assert puzzle.size == 3
    assert puzzle.length == 20


def test_get_puzzle_invalid():
    """Test get_puzzle raises KeyError for invalid key."""
    with pytest.raises(KeyError, match="Unknown puzzle key"):
        get_puzzle("999")
    
    with pytest.raises(KeyError):
        get_puzzle("invalid")
