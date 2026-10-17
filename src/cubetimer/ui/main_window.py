"""Main window for CubeTimer application."""
from PyQt6.QtWidgets import QMainWindow, QLabel, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QKeyEvent

from ..core.timer_engine import TimerEngine, TimerState
from ..core.formatting import format_time
from ..core.scramble.generator import generate_scramble
from .scramble_bar import ScrambleBar


class MainWindow(QMainWindow):
    """Main window displaying the cube timer."""
    
    def __init__(self):
        super().__init__()
        self._engine = TimerEngine()
        self._current_puzzle = "333"  # Fixed puzzle for Phase 2
        self._current_scramble = ""
        self._init_ui()
        self._start_update_timer()
        self._generate_new_scramble()
    
    def _init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("CubeTimer")
        self.setMinimumSize(600, 400)
        
        # Dark background
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        # Central widget with layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Scramble bar at the top
        self._scramble_bar = ScrambleBar()
        self._scramble_bar.new_requested.connect(self._on_new_scramble_requested)
        layout.addWidget(self._scramble_bar)
        
        # Timer label
        self._time_label = QLabel("0.00")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Monospace font, large size
        font = QFont("Monospace", 96)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self._time_label.setFont(font)
        
        layout.addWidget(self._time_label)
        
        # Status bar with instructions
        self.statusBar().showMessage("Giữ Space -> thả để bắt đầu | Esc: reset")
    
    def _start_update_timer(self):
        """Start periodic update timer (10ms cycle)."""
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._on_update)
        self._update_timer.start(10)  # 10ms
    
    def _on_update(self):
        """Called periodically to update engine and display."""
        self._engine.update()
        self._update_display()
    
    def _update_display(self):
        """Update time label with current time and color."""
        state = self._engine.state
        
        # Determine display time
        if state in (TimerState.HOLDING, TimerState.READY):
            display_text = "0.00"
        else:
            display_text = format_time(self._engine.elapsed_ms())
        
        self._time_label.setText(display_text)
        
        # Set color based on state
        if state == TimerState.HOLDING:
            color = Qt.GlobalColor.red
        elif state == TimerState.READY:
            color = Qt.GlobalColor.green
        else:  # IDLE, RUNNING, STOPPED
            color = Qt.GlobalColor.white
        
        palette = self._time_label.palette()
        palette.setColor(QPalette.ColorRole.WindowText, color)
        self._time_label.setPalette(palette)
    
    def _generate_new_scramble(self):
        """Generate a new scramble for the current puzzle."""
        self._current_scramble = generate_scramble(self._current_puzzle)
        self._scramble_bar.set_scramble(self._current_scramble)
    
    def _on_new_scramble_requested(self):
        """Handle request for new scramble from scramble bar."""
        self._generate_new_scramble()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        # Ignore auto-repeat events
        if event.isAutoRepeat():
            return
        
        key = event.key()
        
        if key == Qt.Key.Key_Space:
            # Check if we just stopped the timer
            was_running = self._engine.state == TimerState.RUNNING
            self._engine.on_space_press()
            
            # If we just stopped, generate new scramble for next solve
            if was_running and self._engine.state == TimerState.STOPPED:
                self._generate_new_scramble()
        elif key == Qt.Key.Key_Escape:
            self._engine.reset()
        elif self._engine.state == TimerState.RUNNING:
            # Any other key during RUNNING stops the timer
            self._engine.on_other_key_press()
            # Generate new scramble for next solve
            self._generate_new_scramble()
        
        self._update_display()
    
    def keyReleaseEvent(self, event: QKeyEvent):
        """Handle key release events."""
        # Ignore auto-repeat events
        if event.isAutoRepeat():
            return
        
        if event.key() == Qt.Key.Key_Space:
            self._engine.on_space_release()
            self._update_display()
