from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel,
                             QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QWheelEvent, QMouseEvent
import numpy as np


class Viewport(QGraphicsView):
    """Main viewport for displaying overlay images with zoom and pan."""

    zoom_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._pixmap_item = QGraphicsPixmapItem()
        self._scene.addItem(self._pixmap_item)

        self._zoom = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 10.0

        # Pan state
        self._panning = False
        self._pan_start = None

        # Setup
        self.setRenderHints(self.renderHints())
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setBackgroundBrush(Qt.black)

    def set_image(self, image: np.ndarray):
        """Set the displayed image from numpy array."""
        if image is None:
            return

        # Ensure array is contiguous and make a copy to prevent memory issues
        image = np.ascontiguousarray(image)

        h, w = image.shape[:2]
        if len(image.shape) == 2:
            # Grayscale
            fmt = QImage.Format_Grayscale8
            bytes_per_line = w
        elif image.shape[-1] == 4:
            fmt = QImage.Format_RGBA8888
            bytes_per_line = w * 4
        else:
            fmt = QImage.Format_RGB888
            bytes_per_line = w * 3

        # Create QImage with explicit bytes per line
        qimg = QImage(image.tobytes(), w, h, bytes_per_line, fmt)
        pixmap = QPixmap.fromImage(qimg)
        self._pixmap_item.setPixmap(pixmap)
        self._scene.setSceneRect(0, 0, w, h)

    def wheelEvent(self, event: QWheelEvent):
        """Handle zoom with mouse wheel."""
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else 1 / 1.15

        new_zoom = self._zoom * factor
        if self._min_zoom <= new_zoom <= self._max_zoom:
            self._zoom = new_zoom
            self.scale(factor, factor)
            self.zoom_changed.emit(self._zoom)

    def mousePressEvent(self, event: QMouseEvent):
        """Start panning on middle or right mouse button."""
        if event.button() in (Qt.MiddleButton, Qt.RightButton):
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle panning."""
        if self._panning and self._pan_start:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """End panning."""
        if event.button() in (Qt.MiddleButton, Qt.RightButton):
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.resetTransform()
        self._zoom = 1.0
        self.zoom_changed.emit(self._zoom)

    def set_zoom(self, zoom: float):
        """Set zoom level."""
        if self._min_zoom <= zoom <= self._max_zoom:
            factor = zoom / self._zoom
            self._zoom = zoom
            self.scale(factor, factor)
            self.zoom_changed.emit(self._zoom)

    def fit_in_view(self):
        """Fit image to view."""
        self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)
        # Calculate actual zoom level
        if self._pixmap_item.pixmap().width() > 0:
            view_width = self.viewport().width()
            img_width = self._pixmap_item.pixmap().width()
            self._zoom = view_width / img_width * self.transform().m11()
            self.zoom_changed.emit(self._zoom)

    def get_zoom(self) -> float:
        """Get current zoom level."""
        return self._zoom


class ViewportWidget(QWidget):
    """Viewport with zoom controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._gt_path = ""
        self._pred_path = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Viewport container with path overlay
        viewport_container = QWidget()
        viewport_layout = QVBoxLayout(viewport_container)
        viewport_layout.setContentsMargins(0, 0, 0, 0)
        viewport_layout.setSpacing(0)

        self.viewport = Viewport()
        viewport_layout.addWidget(self.viewport, 1)

        # Path label overlay
        self.path_label = QLabel()
        self.path_label.setStyleSheet(
            "color: #ff80ff; background: rgba(0,0,0,0.5); "
            "padding: 2px 6px; font-size: 10px;"
        )
        self.path_label.setAlignment(Qt.AlignRight)
        self.path_label.hide()
        viewport_layout.addWidget(self.path_label)

        layout.addWidget(viewport_container, 1)

        # Zoom controls
        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(8)

        self.zoom_label = QLabel("ZOOM:")
        zoom_layout.addWidget(self.zoom_label)

        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedWidth(30)
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        zoom_layout.addWidget(self.zoom_out_btn)

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(500)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self._on_slider_change)
        zoom_layout.addWidget(self.zoom_slider)

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedWidth(30)
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        zoom_layout.addWidget(self.zoom_in_btn)

        self.zoom_value_label = QLabel("100%")
        self.zoom_value_label.setFixedWidth(50)
        zoom_layout.addWidget(self.zoom_value_label)

        self.fit_btn = QPushButton("FIT")
        self.fit_btn.setFixedWidth(40)
        self.fit_btn.clicked.connect(self.viewport.fit_in_view)
        zoom_layout.addWidget(self.fit_btn)

        self.reset_btn = QPushButton("1:1")
        self.reset_btn.setFixedWidth(40)
        self.reset_btn.clicked.connect(self.viewport.reset_zoom)
        zoom_layout.addWidget(self.reset_btn)

        layout.addLayout(zoom_layout)

        # Connect signals
        self.viewport.zoom_changed.connect(self._on_zoom_changed)

    def _on_slider_change(self, value):
        zoom = value / 100.0
        self.viewport.set_zoom(zoom)

    def _on_zoom_changed(self, zoom):
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(zoom * 100))
        self.zoom_slider.blockSignals(False)
        self.zoom_value_label.setText(f"{int(zoom * 100)}%")

    def _zoom_in(self):
        self.viewport.set_zoom(self.viewport.get_zoom() * 1.25)

    def _zoom_out(self):
        self.viewport.set_zoom(self.viewport.get_zoom() / 1.25)

    def set_image(self, image: np.ndarray):
        self.viewport.set_image(image)

    def set_paths(self, gt_path: str, pred_path: str):
        """Set and display the current file paths."""
        self._gt_path = gt_path
        self._pred_path = pred_path
        self._update_path_label()

    def _update_path_label(self):
        """Update the path label display."""
        parts = []
        if self._gt_path:
            parts.append(f"GT: {self._gt_path}")
        if self._pred_path:
            parts.append(f"PRED: {self._pred_path}")

        if parts:
            self.path_label.setText(" | ".join(parts))
            self.path_label.show()
        else:
            self.path_label.hide()
