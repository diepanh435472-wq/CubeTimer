"""Scramble generator for NxN cubes using random-move method."""
from __future__ import annotations
import random
from ..puzzles import get_puzzle


def generate_scramble(puzzle_key: str, rng: random.Random | None = None) -> str:
    """
    Generate a random-move scramble for the given puzzle.
    
    Args:
        puzzle_key: Puzzle key (e.g., "333")
        rng: Random number generator (default: new Random instance)
    
    Returns:
        Scramble string with moves separated by spaces
    
    Raises:
        KeyError: If puzzle key is not recognized
    
    Rules:
    - Three axes: (U,D), (R,L), (F,B)
    - Consecutive moves must be on different axes
    - 2x2: only U, R, F (no D, L, B); no wide moves
    - 3x3+: all six faces; 4x4+ includes wide moves (Rw, 3Rw, etc.)
    - Layer depth k ranges from 1 to N//2
    - Suffixes: "", "'", "2" (chosen uniformly)
    """
    if rng is None:
        rng = random.Random()
    
    puzzle = get_puzzle(puzzle_key)
    size = puzzle.size
    length = puzzle.length
    
    # Define axes and faces
    if size == 2:
        # 2x2: only use U, R, F
        axes = [
            ["U"],
            ["R"],
            ["F"],
        ]
    else:
        # 3x3+: all six faces
        axes = [
            ["U", "D"],
            ["R", "L"],
            ["F", "B"],
        ]
    
    # Suffixes for moves
    suffixes = ["", "'", "2"]
    
    moves = []
    last_axis = None
    
    for _ in range(length):
        # Choose axis different from last
        available_axes = [i for i in range(len(axes)) if i != last_axis]
        axis_idx = rng.choice(available_axes)
        last_axis = axis_idx
        
        # Choose face from this axis
        face = rng.choice(axes[axis_idx])
        
        # Choose layer depth k
        if size == 2 or size == 3:
            # No wide moves for 2x2 and 3x3
            k = 1
        else:
            # 4x4+: k from 1 to size//2
            k = rng.randint(1, size // 2)
        
        # Build move notation
        if k == 1:
            move = face
        elif k == 2:
            move = face + "w"
        else:
            move = str(k) + face + "w"
        
        # Add suffix
        suffix = rng.choice(suffixes)
        move += suffix
        
        moves.append(move)
    
    return " ".join(moves)
