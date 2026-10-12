"""Timer engine with state machine for Rubik's cube timer."""
import time
from enum import Enum, auto


class TimerState(Enum):
    """Timer state machine states."""
    IDLE = auto()
    HOLDING = auto()
    READY = auto()
    RUNNING = auto()
    STOPPED = auto()


class TimerEngine:
    """
    Core timer logic without UI dependencies.
    
    State transitions:
    - IDLE + space_press -> HOLDING
    - HOLDING + space_release (< threshold) -> IDLE
    - HOLDING + update (>= threshold) -> READY
    - READY + space_release -> RUNNING
    - RUNNING + space_press/other_key -> STOPPED
    - STOPPED + space_press -> HOLDING
    """
    
    def __init__(self, clock=None, hold_threshold=0.3):
        """
        Initialize timer engine.
        
        Args:
            clock: Callable that returns current time in seconds (default: time.perf_counter)
            hold_threshold: Seconds to hold space before ready state (default: 0.3)
        """
        self._clock = clock if clock is not None else time.perf_counter
        self._hold_threshold = hold_threshold
        self._state = TimerState.IDLE
        self._last_time_ms = None
        self._hold_start = None
        self._run_start = None
        self._stopped_time_ms = None
    
    @property
    def state(self):
        """Current timer state."""
        return self._state
    
    @property
    def last_time_ms(self):
        """Last completed solve time in milliseconds, or None."""
        return self._last_time_ms
    
    def on_space_press(self):
        """Handle space key press event."""
        if self._state == TimerState.IDLE:
            self._state = TimerState.HOLDING
            self._hold_start = self._clock()
        elif self._state == TimerState.RUNNING:
            # Stop immediately on key press
            elapsed = int((self._clock() - self._run_start) * 1000)
            self._last_time_ms = elapsed
            self._stopped_time_ms = elapsed
            self._state = TimerState.STOPPED
        elif self._state == TimerState.STOPPED:
            # Start new solve
            self._state = TimerState.HOLDING
            self._hold_start = self._clock()
    
    def on_space_release(self):
        """Handle space key release event."""
        if self._state == TimerState.HOLDING:
            # Released too early
            self._state = TimerState.IDLE
            self._hold_start = None
        elif self._state == TimerState.READY:
            # Start running
            self._state = TimerState.RUNNING
            self._run_start = self._clock()
        # STOPPED + space_release: ignore (this is the release from the stop key press)
    
    def on_other_key_press(self):
        """Handle other (non-space) key press during RUNNING."""
        if self._state == TimerState.RUNNING:
            elapsed = int((self._clock() - self._run_start) * 1000)
            self._last_time_ms = elapsed
            self._stopped_time_ms = elapsed
            self._state = TimerState.STOPPED
    
    def reset(self):
        """Reset to IDLE state and clear display."""
        self._state = TimerState.IDLE
        self._last_time_ms = None
        self._hold_start = None
        self._run_start = None
        self._stopped_time_ms = None
    
    def elapsed_ms(self):
        """
        Get elapsed time in milliseconds.
        
        Returns:
            int: RUNNING: time since start; STOPPED: final time; others: 0
        """
        if self._state == TimerState.RUNNING:
            return int((self._clock() - self._run_start) * 1000)
        elif self._state == TimerState.STOPPED:
            return self._stopped_time_ms
        return 0
    
    def update(self):
        """
        Update timer state. Call periodically from UI.
        
        Transitions HOLDING to READY after hold_threshold seconds.
        """
        if self._state == TimerState.HOLDING:
            if self._clock() - self._hold_start >= self._hold_threshold:
                self._state = TimerState.READY
