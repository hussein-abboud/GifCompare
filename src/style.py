"""Brutalist minimal styling for the GIF Compare application."""

BRUTALIST_STYLE = """
QMainWindow {
    background-color: #1a1a1a;
}

QWidget {
    background-color: #1a1a1a;
    color: #e0e0e0;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
}

QLabel {
    color: #e0e0e0;
    padding: 2px;
}

QPushButton {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #404040;
    padding: 6px 12px;
    min-width: 60px;
}

QPushButton:hover {
    background-color: #404040;
    border-color: #606060;
}

QPushButton:pressed {
    background-color: #505050;
}

QPushButton:disabled {
    background-color: #1a1a1a;
    color: #606060;
    border-color: #303030;
}

QLineEdit {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #404040;
    padding: 4px 8px;
    selection-background-color: #505050;
}

QLineEdit:focus {
    border-color: #808080;
}

QComboBox {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #404040;
    padding: 4px 8px;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #606060;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid #808080;
    margin-right: 6px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #404040;
    selection-background-color: #404040;
}

QSpinBox, QDoubleSpinBox {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #404040;
    padding: 4px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #404040;
    border: none;
    width: 16px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #505050;
}

QSlider::groove:horizontal {
    background-color: #2d2d2d;
    height: 6px;
    border: 1px solid #404040;
}

QSlider::handle:horizontal {
    background-color: #808080;
    width: 14px;
    margin: -4px 0;
    border: 1px solid #606060;
}

QSlider::handle:horizontal:hover {
    background-color: #a0a0a0;
}

QSlider::sub-page:horizontal {
    background-color: #505050;
}

QTabWidget::pane {
    border: 1px solid #404040;
    background-color: #1a1a1a;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #a0a0a0;
    border: 1px solid #404040;
    padding: 8px 16px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border-bottom-color: #1a1a1a;
}

QTabBar::tab:hover:!selected {
    background-color: #353535;
}

QScrollBar:horizontal {
    background-color: #1a1a1a;
    height: 12px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #404040;
    min-width: 30px;
    border: none;
}

QScrollBar::handle:horizontal:hover {
    background-color: #505050;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QScrollBar:vertical {
    background-color: #1a1a1a;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #404040;
    min-height: 30px;
    border: none;
}

QScrollBar::handle:vertical:hover {
    background-color: #505050;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QTableWidget {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border: 1px solid #404040;
    gridline-color: #303030;
    selection-background-color: #404040;
}

QTableWidget::item {
    padding: 4px;
}

QHeaderView::section {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #404040;
    padding: 6px;
}

QListWidget {
    background-color: #1a1a1a;
    color: #e0e0e0;
    border: 1px solid #404040;
    selection-background-color: #404040;
}

QListWidget::item {
    padding: 4px;
}

QListWidget::item:hover {
    background-color: #2d2d2d;
}

QCheckBox {
    color: #e0e0e0;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    background-color: #2d2d2d;
    border: 1px solid #404040;
}

QCheckBox::indicator:checked {
    background-color: #606060;
}

QCheckBox::indicator:hover {
    border-color: #606060;
}

QRadioButton {
    color: #e0e0e0;
    spacing: 6px;
}

QRadioButton::indicator {
    width: 14px;
    height: 14px;
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 7px;
}

QRadioButton::indicator:checked {
    background-color: #606060;
}

QRadioButton::indicator:hover {
    border-color: #606060;
}

QGroupBox {
    border: 1px solid #404040;
    margin-top: 12px;
    padding-top: 8px;
}

QGroupBox::title {
    color: #a0a0a0;
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}

QSplitter::handle {
    background-color: #404040;
}

QSplitter::handle:hover {
    background-color: #606060;
}

QToolTip {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #404040;
    padding: 4px;
}

QProgressBar {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    text-align: center;
    color: #e0e0e0;
}

QProgressBar::chunk {
    background-color: #505050;
}

QDialog {
    background-color: #1a1a1a;
}

QMessageBox {
    background-color: #1a1a1a;
}
"""
