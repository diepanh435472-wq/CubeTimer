"""Puzzle specifications for cube timer."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PuzzleSpec:
    """Specification for a twisty puzzle."""
    key: str        # "222", "333", etc.
    name: str       # "2x2x2", "3x3x3", etc.
    size: int       # 2, 3, 4, 5, 6, 7
    length: int     # number of moves in scramble


# Puzzle definitions: key -> (size, scramble_length)
PUZZLES = {
    "222": PuzzleSpec("222", "2x2x2", 2, 11),
    "333": PuzzleSpec("333", "3x3x3", 3, 20),
    "444": PuzzleSpec("444", "4x4x4", 4, 40),
    "555": PuzzleSpec("555", "5x5x5", 5, 60),
    "666": PuzzleSpec("666", "6x6x6", 6, 80),
    "777": PuzzleSpec("777", "7x7x7", 7, 100),
}


def get_puzzle(key: str) -> PuzzleSpec:
    """
    Get puzzle specification by key.
    
    Args:
        key: Puzzle key (e.g., "333")
    
    Returns:
        PuzzleSpec for the requested puzzle
    
    Raises:
        KeyError: If puzzle key is not recognized
    """
    if key not in PUZZLES:
        raise KeyError(f"Unknown puzzle key: {key}")
    return PUZZLES[key]
