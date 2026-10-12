"""Tests for timer engine state machine."""
import pytest
from cubetimer.core.timer_engine import TimerEngine, TimerState


class FakeClock:
    """Fake clock for testing with manual time control."""
    
    def __init__(self):
        self.current_time = 0.0
    
    def __call__(self):
        return self.current_time
    
    def advance(self, seconds):
        """Advance time by given seconds."""
        self.current_time += seconds


def test_hold_sufficient_then_release_runs():
    """Test: Hold >= 0.3s then release -> RUNNING."""
    clock = FakeClock()
    engine = TimerEngine(clock=clock, hold_threshold=0.3)
    
    # Initial state
    assert engine.state == TimerState.IDLE
    
    # Press space
    engine.on_space_press()
    assert engine.state == TimerState.HOLDING
    
    # Advance time to 0.1s (not enough)
    clock.advance(0.1)
    engine.update()
    assert engine.state == TimerState.HOLDING
    
    # Advance to 0.3s total (threshold reached)
    clock.advance(0.2)
    engine.update()
    assert engine.state == TimerState.READY
    
    # Release space
    engine.on_space_release()
    assert engine.state == TimerState.RUNNING


def test_hold_insufficient_then_release_returns_idle():
    """Test: Hold < 0.3s then release -> IDLE (cancelled)."""
    clock = FakeClock()
    engine = TimerEngine(clock=clock, hold_threshold=0.3)
    
    # Press space
    engine.on_space_press()
    assert engine.state == TimerState.HOLDING
    
    # Advance only 0.1s
    clock.advance(0.1)
    engine.update()
    assert engine.state == TimerState.HOLDING
    
    # Release too early
    engine.on_space_release()
    assert engine.state == TimerState.IDLE


def test_running_space_press_stops():
    """Test: RUNNING + space_press -> STOPPED with correct time."""
    clock = FakeClock()
    engine = TimerEngine(clock=clock, hold_threshold=0.3)
    
    # Get to RUNNING state
    engine.on_space_press()
    clock.advance(0.3)
    engine.update()
    engine.on_space_release()
    assert engine.state == TimerState.RUNNING
    
    # Run for 5.5 seconds
    clock.advance(5.5)
    
    # Press space to stop
    engine.on_space_press()
    assert engine.state == TimerState.STOPPED
    assert engine.last_time_ms == 5500
    assert engine.elapsed_ms() == 5500


def test_stopped_space_release_ignored():
    """Test: After STOPPED, space_release doesn't change state."""
    clock = FakeClock()
    engine = TimerEngine(clock=clock, hold_threshold=0.3)
    
    # Get to STOPPED state
    engine.on_space_press()
    clock.advance(0.3)
    engine.update()
    engine.on_space_release()
    clock.advance(2.0)
    engine.on_space_press()  # Stop
    
    assert engine.state == TimerState.STOPPED
    
    # Release space (from the stop key press)
    engine.on_space_release()
    assert engine.state == TimerState.STOPPED


def test_stopped_space_press_new_solve():
    """Test: STOPPED + space_press -> HOLDING (new solve)."""
    clock = FakeClock()
    engine = TimerEngine(clock=clock, hold_threshold=0.3)
    
    # Get to STOPPED state
    engine.on_space_press()
    clock.advance(0.3)
    engine.update()
    engine.on_space_release()
    clock.advance(1.0)
    engine.on_space_press()  # Stop
    
    assert engine.state == TimerState.STOPPED
    old_time = engine.last_time_ms
    
    # Start new solve
    engine.on_space_press()
    assert engine.state == TimerState.HOLDING
    # last_time_ms should still contain previous solve
    assert engine.last_time_ms == old_time


def test_other_key_stops_running():
    """Test: Other key press during RUNNING also stops timer."""
    clock = FakeClock()
    engine = TimerEngine(clock=clock, hold_threshold=0.3)
    
    # Get to RUNNING state
    engine.on_space_press()
    clock.advance(0.3)
    engine.update()
    engine.on_space_release()
    assert engine.state == TimerState.RUNNING
    
    # Run for 3 seconds
    clock.advance(3.0)
    
    # Press any other key
    engine.on_other_key_press()
    assert engine.state == TimerState.STOPPED
    assert engine.last_time_ms == 3000


def test_reset_from_any_state():
    """Test: reset() returns to IDLE from any state."""
    # Test reset from HOLDING
    clock = FakeClock()
    engine = TimerEngine(clock=clock)
    engine.on_space_press()
    assert engine.state == TimerState.HOLDING
    engine.reset()
    assert engine.state == TimerState.IDLE
    assert engine.last_time_ms is None
    
    # Test reset from READY
    clock = FakeClock()
    engine = TimerEngine(clock=clock)
    engine.on_space_press()
    clock.advance(0.3)
    engine.update()
    assert engine.state == TimerState.READY
    engine.reset()
    assert engine.state == TimerState.IDLE
    
    # Test reset from RUNNING
    clock = FakeClock()
    engine = TimerEngine(clock=clock)
    engine.on_space_press()
    clock.advance(0.3)
    engine.update()
    engine.on_space_release()
    assert engine.state == TimerState.RUNNING
    engine.reset()
    assert engine.state == TimerState.IDLE
    
    # Test reset from STOPPED
    clock = FakeClock()
    engine = TimerEngine(clock=clock)
    engine.on_space_press()
    clock.advance(0.3)
    engine.update()
    engine.on_space_release()
    clock.advance(1.0)
    engine.on_space_press()
    assert engine.state == TimerState.STOPPED
    engine.reset()
    assert engine.state == TimerState.IDLE
    assert engine.last_time_ms is None


def test_elapsed_ms_in_different_states():
    """Test elapsed_ms() returns correct values in different states."""
    clock = FakeClock()
    engine = TimerEngine(clock=clock, hold_threshold=0.3)
    
    # IDLE: should return 0
    assert engine.elapsed_ms() == 0
    
    # HOLDING: should return 0
    engine.on_space_press()
    assert engine.elapsed_ms() == 0
    
    # READY: should return 0
    clock.advance(0.3)
    engine.update()
    assert engine.elapsed_ms() == 0
    
    # RUNNING: should return elapsed time
    engine.on_space_release()
    clock.advance(2.5)
    assert engine.elapsed_ms() == 2500
    
    # STOPPED: should return final time
    engine.on_space_press()
    assert engine.state == TimerState.STOPPED
    assert engine.elapsed_ms() == 2500
    
    # Time shouldn't change after stopping
    clock.advance(1.0)
    assert engine.elapsed_ms() == 2500
