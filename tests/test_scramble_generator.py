"""Tests for scramble generator."""
import pytest
import random
import re
from cubetimer.core.scramble.generator import generate_scramble
from cubetimer.core.puzzles import PUZZLES


def test_scramble_length_correct():
    """Test that scramble has correct number of moves for each puzzle."""
    for key, puzzle in PUZZLES.items():
        scramble = generate_scramble(key)
        moves = scramble.split()
        assert len(moves) == puzzle.length, f"Puzzle {key} expected {puzzle.length} moves, got {len(moves)}"


def test_no_consecutive_same_axis():
    """Test that no two consecutive moves are on the same axis."""
    # Define axes for each face
    axes = {
        'U': 0, 'D': 0,
        'R': 1, 'L': 1,
        'F': 2, 'B': 2,
    }
    
    def get_face(move):
        """Extract face letter from move (handles multi-layer notation)."""
        # Move format: [digits][FACE][w][suffix]
        # Find the first uppercase letter
        for char in move:
            if char in 'URLFBD':
                return char
        return None
    
    for key in PUZZLES.keys():
        scramble = generate_scramble(key)
        moves = scramble.split()
        
        for i in range(len(moves) - 1):
            # Extract face from move
            face1 = get_face(moves[i])
            face2 = get_face(moves[i + 1])
            
            # Check they're on different axes
            assert axes[face1] != axes[face2], \
                f"Consecutive moves {moves[i]} and {moves[i+1]} on same axis in {key}"


def test_2x2_only_uses_urf():
    """Test that 2x2 scrambles only use U, R, F faces."""
    for _ in range(10):
        scramble = generate_scramble("222")
        moves = scramble.split()
        
        for move in moves:
            face = move[0]
            assert face in ['U', 'R', 'F'], \
                f"2x2 scramble contains invalid face: {move}"


def test_move_syntax_valid():
    """Test that all moves match valid syntax pattern."""
    # Pattern: optional digits, face letter, optional 'w', optional suffix
    pattern = re.compile(r"^(\d*)([URLFBD])w?(['2]?)$")
    
    for key in PUZZLES.keys():
        scramble = generate_scramble(key)
        moves = scramble.split()
        
        for move in moves:
            assert pattern.match(move), \
                f"Invalid move syntax: {move} in puzzle {key}"


def test_same_seed_same_result():
    """Test that same seed produces same scramble."""
    seed = 42
    
    for key in PUZZLES.keys():
        rng1 = random.Random(seed)
        scramble1 = generate_scramble(key, rng1)
        
        rng2 = random.Random(seed)
        scramble2 = generate_scramble(key, rng2)
        
        assert scramble1 == scramble2, \
            f"Same seed produced different scrambles for {key}"


def test_different_seed_different_result():
    """Test that different seeds usually produce different scrambles."""
    scramble1 = generate_scramble("333", random.Random(1))
    scramble2 = generate_scramble("333", random.Random(2))
    
    # Very unlikely to be the same with 20 random moves
    assert scramble1 != scramble2


def test_4x4_has_wide_moves():
    """Test that 4x4 can generate wide moves (Rw)."""
    # Generate many scrambles and check at least one has a wide move
    found_wide = False
    
    for i in range(50):
        scramble = generate_scramble("444", random.Random(i))
        if "w" in scramble:
            found_wide = True
            break
    
    assert found_wide, "4x4 should generate wide moves"


def test_5x5_has_multi_layer_moves():
    """Test that 5x5+ can generate multi-layer moves (3Rw)."""
    # For 5x5, we can have 1Rw (=R), 2Rw (=Rw), so no explicit 3
    # But moves with k=2 should appear as "Rw"
    found_wide = False
    
    for i in range(50):
        scramble = generate_scramble("555", random.Random(i))
        if "w" in scramble:
            found_wide = True
            break
    
    assert found_wide, "5x5 should generate wide moves"


def test_6x6_has_explicit_multi_layer():
    """Test that 6x6+ can generate explicit multi-layer moves (3Rw)."""
    # For 6x6, k can be 1, 2, or 3, so 3Rw is possible
    found_three_layer = False
    
    for i in range(100):
        scramble = generate_scramble("666", random.Random(i))
        if "3" in scramble and "w" in scramble:
            found_three_layer = True
            break
    
    assert found_three_layer, "6x6 should generate 3-layer moves"


def test_7x7_has_explicit_multi_layer():
    """Test that 7x7 can generate explicit multi-layer moves."""
    # For 7x7, k can be 1, 2, or 3, so 3Rw is possible
    found_three_layer = False
    
    for i in range(100):
        scramble = generate_scramble("777", random.Random(i))
        if "3" in scramble and "w" in scramble:
            found_three_layer = True
            break
    
    assert found_three_layer, "7x7 should generate 3-layer moves"


def test_scramble_has_all_suffixes():
    """Test that scrambles include all types of suffixes."""
    # Generate many scrambles and check we see all suffixes
    suffixes_seen = set()
    
    for i in range(50):
        scramble = generate_scramble("333", random.Random(i))
        moves = scramble.split()
        
        for move in moves:
            # Check suffix
            if move.endswith("'"):
                suffixes_seen.add("'")
            elif move.endswith("2"):
                suffixes_seen.add("2")
            else:
                suffixes_seen.add("")
    
    assert suffixes_seen == {"", "'", "2"}, \
        "Should see all suffix types in generated scrambles"


def test_invalid_puzzle_raises_error():
    """Test that invalid puzzle key raises KeyError."""
    with pytest.raises(KeyError):
        generate_scramble("999")
