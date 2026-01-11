from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QSlider,
                             QLabel, QComboBox, QSpinBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal


class PlaybackControls(QWidget):
    """Playback controls for GIF animation."""

    frame_changed = pyqtSignal(int)
    playback_started = pyqtSignal()
    playback_stopped = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._frame_count = 0
        self._current_frame = 0
        self._playing = False
        self._base_interval = 100  # ms
        self._speed = 1.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Frame indicator
        self.frame_label = QLabel("FRAME:")
        layout.addWidget(self.frame_label)

        self.frame_spinbox = QSpinBox()
        self.frame_spinbox.setMinimum(0)
        self.frame_spinbox.setMaximum(0)
        self.frame_spinbox.setFixedWidth(70)
        self.frame_spinbox.valueChanged.connect(self._on_spinbox_change)
        layout.addWidget(self.frame_spinbox)

        self.total_label = QLabel("/ 0")
        self.total_label.setFixedWidth(50)
        layout.addWidget(self.total_label)

        layout.addSpacing(10)

        # Navigation buttons
        self.first_btn = QPushButton("|<")
        self.first_btn.setFixedWidth(30)
        self.first_btn.clicked.connect(self.go_to_first)
        layout.addWidget(self.first_btn)

        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedWidth(30)
        self.prev_btn.clicked.connect(self.prev_frame)
        layout.addWidget(self.prev_btn)

        self.play_btn = QPushButton(">")
        self.play_btn.setFixedWidth(40)
        self.play_btn.clicked.connect(self.toggle_play)
        layout.addWidget(self.play_btn)

        self.next_btn = QPushButton(">")
        self.next_btn.setFixedWidth(30)
        self.next_btn.clicked.connect(self.next_frame)
        layout.addWidget(self.next_btn)

        self.last_btn = QPushButton(">|")
        self.last_btn.setFixedWidth(30)
        self.last_btn.clicked.connect(self.go_to_last)
        layout.addWidget(self.last_btn)

        layout.addSpacing(10)

        # Speed control
        self.speed_label = QLabel("SPEED:")
        layout.addWidget(self.speed_label)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems([
            "0.01x", "0.025x", "0.05x", "0.1x", "0.2x", "0.25x",
            "0.5x", "0.75x", "1.0x", "1.5x", "2.0x", "4.0x", "8.0x"
        ])
        self.speed_combo.setCurrentIndex(1)  # 0.025x
        self._speed = 0.025
        self.speed_combo.currentTextChanged.connect(self._on_speed_change)
        layout.addWidget(self.speed_combo)

        layout.addStretch()

    def _on_timer(self):
        try:
            if self._frame_count > 0:
                next_frame = (self._current_frame + 1) % self._frame_count
                self.set_frame(next_frame)
        except Exception as e:
            print(f"Timer error: {e}")
            self.stop()

    def _on_spinbox_change(self, value):
        if value != self._current_frame:
            self.set_frame(value)

    def _on_speed_change(self, text):
        self._speed = float(text.replace("x", ""))
        if self._playing:
            interval = int(self._base_interval / self._speed)
            self._timer.setInterval(max(10, interval))

    def set_frame_count(self, count: int):
        """Set total number of frames."""
        self._frame_count = count
        self.frame_spinbox.setMaximum(max(0, count - 1))
        self.total_label.setText(f"/ {count}")
        if self._current_frame >= count:
            self.set_frame(0)

    def set_base_interval(self, interval: int):
        """Set base frame interval in milliseconds."""
        self._base_interval = interval
        if self._playing:
            self._timer.setInterval(max(10, int(interval / self._speed)))

    def set_frame(self, frame: int, emit: bool = True):
        """Set current frame."""
        if self._frame_count == 0:
            return
        frame = max(0, min(frame, self._frame_count - 1))
        self._current_frame = frame
        self.frame_spinbox.blockSignals(True)
        self.frame_spinbox.setValue(frame)
        self.frame_spinbox.blockSignals(False)
        if emit:
            self.frame_changed.emit(frame)

    def get_frame(self) -> int:
        """Get current frame index."""
        return self._current_frame

    def toggle_play(self):
        """Toggle playback."""
        if self._playing:
            self.stop()
        else:
            self.play()

    def play(self):
        """Start playback."""
        if self._frame_count > 0:
            self._playing = True
            interval = int(self._base_interval / self._speed)
            self._timer.start(max(10, interval))
            self.play_btn.setText("||")
            self.playback_started.emit()

    def stop(self):
        """Stop playback."""
        self._playing = False
        self._timer.stop()
        self.play_btn.setText(">")
        self.playback_stopped.emit()

    def is_playing(self) -> bool:
        """Check if playing."""
        return self._playing

    def next_frame(self):
        """Go to next frame."""
        if self._frame_count > 0:
            self.set_frame((self._current_frame + 1) % self._frame_count)

    def prev_frame(self):
        """Go to previous frame."""
        if self._frame_count > 0:
            self.set_frame((self._current_frame - 1) % self._frame_count)

    def go_to_first(self):
        """Go to first frame."""
        self.set_frame(0)

    def go_to_last(self):
        """Go to last frame."""
        if self._frame_count > 0:
            self.set_frame(self._frame_count - 1)


class FrameSlider(QWidget):
    """Frame slider for seeking through animation."""

    frame_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.valueChanged.connect(self._on_change)
        layout.addWidget(self.slider)

    def _on_change(self, value):
        self.frame_changed.emit(value)

    def set_frame_count(self, count: int):
        """Set total number of frames."""
        self.slider.setMaximum(max(0, count - 1))

    def set_frame(self, frame: int):
        """Set current frame without emitting signal."""
        self.slider.blockSignals(True)
        self.slider.setValue(frame)
        self.slider.blockSignals(False)

    def get_frame(self) -> int:
        """Get current frame."""
        return self.slider.value()
