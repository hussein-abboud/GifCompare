from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QScrollArea,
                             QPushButton, QLabel, QFileDialog, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor
import numpy as np
from typing import List, Optional


class FrameThumbnail(QLabel):
    """Single frame thumbnail widget."""

    clicked = pyqtSignal(int)

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self._selected = False
        self.setFixedSize(64, 64)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 2px solid #404040; background: #2d2d2d;")

    def set_image(self, image: np.ndarray):
        """Set thumbnail image from numpy array."""
        if image is None:
            return

        image = np.ascontiguousarray(image)
        h, w = image.shape[:2]

        if image.shape[-1] == 4:
            fmt = QImage.Format_RGBA8888
            bytes_per_line = w * 4
        else:
            fmt = QImage.Format_RGB888
            bytes_per_line = w * 3

        qimg = QImage(image.tobytes(), w, h, bytes_per_line, fmt)
        pixmap = QPixmap.fromImage(qimg).scaled(
            60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.setPixmap(pixmap)

    def set_selected(self, selected: bool):
        """Set selection state."""
        self._selected = selected
        if selected:
            self.setStyleSheet("border: 2px solid #ffffff; background: #404040;")
        else:
            self.setStyleSheet("border: 2px solid #404040; background: #2d2d2d;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)


class FrameStrip(QWidget):
    """Horizontal strip of frame thumbnails."""

    frame_selected = pyqtSignal(int)
    frame_deleted = pyqtSignal(int)
    frame_add_requested = pyqtSignal(int)

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self._label = label
        self._thumbnails: List[FrameThumbnail] = []
        self._selected_index = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.label = QLabel(self._label)
        self.label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.label)

        header_layout.addStretch()

        self.add_btn = QPushButton("+ ADD")
        self.add_btn.setFixedWidth(60)
        self.add_btn.clicked.connect(self._on_add)
        header_layout.addWidget(self.add_btn)

        self.del_btn = QPushButton("- DEL")
        self.del_btn.setFixedWidth(60)
        self.del_btn.clicked.connect(self._on_delete)
        header_layout.addWidget(self.del_btn)

        self.total_label = QLabel("TOTAL: 0")
        self.total_label.setFixedWidth(80)
        header_layout.addWidget(self.total_label)

        layout.addLayout(header_layout)

        # Scroll area for thumbnails
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFixedHeight(90)

        self.scroll_widget = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_layout.setSpacing(4)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

    def set_thumbnails(self, thumbnails: List[np.ndarray]):
        """Set all thumbnails."""
        # Clear existing
        for thumb in self._thumbnails:
            self.scroll_layout.removeWidget(thumb)
            thumb.deleteLater()
        self._thumbnails.clear()

        # Add new
        for i, img in enumerate(thumbnails):
            thumb = FrameThumbnail(i)
            thumb.set_image(img)
            thumb.clicked.connect(self._on_thumb_clicked)
            self._thumbnails.append(thumb)
            self.scroll_layout.insertWidget(i, thumb)

        self.total_label.setText(f"TOTAL: {len(thumbnails)}")

        if self._thumbnails:
            self.set_selected(min(self._selected_index, len(self._thumbnails) - 1))

    def update_thumbnail(self, index: int, image: np.ndarray):
        """Update a single thumbnail."""
        if 0 <= index < len(self._thumbnails):
            self._thumbnails[index].set_image(image)

    def set_selected(self, index: int):
        """Set selected frame."""
        if not self._thumbnails:
            return
        # Clamp index to valid range
        index = max(0, min(index, len(self._thumbnails) - 1))
        # Deselect old
        if 0 <= self._selected_index < len(self._thumbnails):
            self._thumbnails[self._selected_index].set_selected(False)
        # Select new
        self._selected_index = index
        self._thumbnails[index].set_selected(True)
        # Scroll to visible
        self.scroll_area.ensureWidgetVisible(self._thumbnails[index])

    def _on_thumb_clicked(self, index: int):
        self.set_selected(index)
        self.frame_selected.emit(index)

    def _on_add(self):
        self.frame_add_requested.emit(self._selected_index + 1)

    def _on_delete(self):
        if len(self._thumbnails) > 1:
            self.frame_deleted.emit(self._selected_index)

    def get_selected(self) -> int:
        """Get selected frame index."""
        return self._selected_index

    def get_frame_count(self) -> int:
        """Get total frame count."""
        return len(self._thumbnails)
