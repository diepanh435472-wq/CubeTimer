"""Scramble display bar with navigation buttons."""
from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal


class ScrambleBar(QWidget):
    """
    Widget displaying scramble with previous/new buttons.
    
    Signals:
        new_requested: User clicked "new" button
        previous_requested: User clicked "previous" button
    """
    
    new_requested = pyqtSignal()
    previous_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components."""
        layout = QHBoxLayout(self)
        
        # Previous button
        self._prev_button = QPushButton("<")
        self._prev_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._prev_button.setMaximumWidth(40)
        self._prev_button.clicked.connect(self.previous_requested.emit)
        self._prev_button.setEnabled(False)  # Disabled for now (no history yet)
        layout.addWidget(self._prev_button)
        
        # Scramble label
        self._scramble_label = QLabel("Ready")
        self._scramble_label.setWordWrap(True)
        self._scramble_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Medium font size for scramble
        font = self._scramble_label.font()
        font.setPointSize(14)
        self._scramble_label.setFont(font)
        
        layout.addWidget(self._scramble_label, stretch=1)
        
        # New button
        self._new_button = QPushButton("New")
        self._new_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._new_button.setMaximumWidth(60)
        self._new_button.clicked.connect(self.new_requested.emit)
        layout.addWidget(self._new_button)
    
    def set_scramble(self, scramble: str):
        """Set the scramble text to display."""
        self._scramble_label.setText(scramble)
    
    def get_scramble(self) -> str:
        """Get the current scramble text."""
        return self._scramble_label.text()
