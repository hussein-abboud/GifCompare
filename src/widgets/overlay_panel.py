from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QRadioButton, QButtonGroup, QCheckBox, QSpinBox,
                             QDoubleSpinBox, QLabel, QPushButton, QColorDialog)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor
from src.overlay_engine import OverlayMode


class OverlayModePanel(QWidget):
    """Panel for selecting overlay mode."""

    mode_changed = pyqtSignal(OverlayMode)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("OVERLAY MODE")
        group_layout = QHBoxLayout(group)

        # Left column
        left_layout = QVBoxLayout()
        self.normal_radio = QRadioButton("NORMAL")
        self.dual_color_radio = QRadioButton("DUAL COLOR")
        self.blend_radio = QRadioButton("BLEND 50%")
        self.side_by_side_radio = QRadioButton("SIDE BY SIDE")
        self.side_by_side_radio.setChecked(True)
        left_layout.addWidget(self.normal_radio)
        left_layout.addWidget(self.dual_color_radio)
        left_layout.addWidget(self.blend_radio)
        left_layout.addWidget(self.side_by_side_radio)

        # Right column
        right_layout = QVBoxLayout()
        self.difference_radio = QRadioButton("DIFFERENCE")
        self.flicker_radio = QRadioButton("FLICKER")
        self.checkerboard_radio = QRadioButton("CHECKERBOARD")
        right_layout.addWidget(self.difference_radio)
        right_layout.addWidget(self.flicker_radio)
        right_layout.addWidget(self.checkerboard_radio)
        right_layout.addStretch()

        group_layout.addLayout(left_layout)
        group_layout.addLayout(right_layout)
        layout.addWidget(group)

        # Button group
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.normal_radio, 0)
        self.button_group.addButton(self.dual_color_radio, 1)
        self.button_group.addButton(self.difference_radio, 2)
        self.button_group.addButton(self.blend_radio, 3)
        self.button_group.addButton(self.flicker_radio, 4)
        self.button_group.addButton(self.checkerboard_radio, 5)
        self.button_group.addButton(self.side_by_side_radio, 6)
        self.button_group.buttonClicked.connect(self._on_mode_changed)

        # Mode mapping
        self._modes = {
            0: OverlayMode.NORMAL,
            1: OverlayMode.DUAL_COLOR,
            2: OverlayMode.DIFFERENCE,
            3: OverlayMode.BLEND,
            4: OverlayMode.FLICKER,
            5: OverlayMode.CHECKERBOARD,
            6: OverlayMode.SIDE_BY_SIDE,
        }

    def _on_mode_changed(self, button):
        mode_id = self.button_group.id(button)
        mode = self._modes.get(mode_id, OverlayMode.BLEND)
        self.mode_changed.emit(mode)

    def get_mode(self) -> OverlayMode:
        """Get current mode."""
        mode_id = self.button_group.checkedId()
        return self._modes.get(mode_id, OverlayMode.BLEND)


class GridOverlayPanel(QWidget):
    """Panel for grid overlay settings."""

    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = (128, 128, 128)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("GRID OVERLAY")
        group_layout = QVBoxLayout(group)

        # Enable checkbox
        self.enable_check = QCheckBox("ENABLE GRID")
        self.enable_check.stateChanged.connect(self._on_change)
        group_layout.addWidget(self.enable_check)

        # Size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("SIZE:"))
        self.size_spin = QSpinBox()
        self.size_spin.setMinimum(4)
        self.size_spin.setMaximum(256)
        self.size_spin.setValue(32)
        self.size_spin.setSuffix(" px")
        self.size_spin.valueChanged.connect(self._on_change)
        size_layout.addWidget(self.size_spin)
        size_layout.addStretch()
        group_layout.addLayout(size_layout)

        # Color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("COLOR:"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 24)
        self._update_color_btn()
        self.color_btn.clicked.connect(self._pick_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        group_layout.addLayout(color_layout)

        # Opacity
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("OPACITY:"))
        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setMinimum(0.0)
        self.opacity_spin.setMaximum(1.0)
        self.opacity_spin.setSingleStep(0.1)
        self.opacity_spin.setValue(0.5)
        self.opacity_spin.valueChanged.connect(self._on_change)
        opacity_layout.addWidget(self.opacity_spin)
        opacity_layout.addStretch()
        group_layout.addLayout(opacity_layout)

        layout.addWidget(group)

    def _update_color_btn(self):
        r, g, b = self._color
        self.color_btn.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); border: 1px solid #606060;"
        )

    def _pick_color(self):
        color = QColorDialog.getColor(
            QColor(*self._color), self, "Select Grid Color"
        )
        if color.isValid():
            self._color = (color.red(), color.green(), color.blue())
            self._update_color_btn()
            self._on_change()

    def _on_change(self):
        self.settings_changed.emit()

    def is_enabled(self) -> bool:
        return self.enable_check.isChecked()

    def get_size(self) -> int:
        return self.size_spin.value()

    def get_color(self) -> tuple:
        return self._color

    def get_opacity(self) -> float:
        return self.opacity_spin.value()
