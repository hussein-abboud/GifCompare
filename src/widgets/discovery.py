from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QListWidget, QListWidgetItem, QLabel,
                             QFileDialog, QProgressDialog, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal
from pathlib import Path
from typing import List, Set
import re


class DiscoveryDialog(QDialog):
    """Dialog for discovering similar files in subdirectories."""

    files_selected = pyqtSignal(list)  # List of file paths

    def __init__(self, base_path: str = "", pattern: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("DISCOVER SIMILAR FILES")
        self.setMinimumSize(500, 400)
        self._base_path = base_path or str(Path.cwd())
        self._pattern = pattern
        self._found_files: List[Path] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Base path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("BASE PATH:"))
        self.path_edit = QLineEdit(self._base_path)
        path_layout.addWidget(self.path_edit)
        self.browse_btn = QPushButton("...")
        self.browse_btn.setFixedWidth(30)
        self.browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(self.browse_btn)
        layout.addLayout(path_layout)

        # Pattern
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(QLabel("PATTERN:"))
        self.pattern_edit = QLineEdit(self._pattern)
        self.pattern_edit.setPlaceholderText("e.g., video_001*.gif")
        pattern_layout.addWidget(self.pattern_edit)
        layout.addLayout(pattern_layout)

        # Scan button
        self.scan_btn = QPushButton("SCAN")
        self.scan_btn.clicked.connect(self._scan)
        layout.addWidget(self.scan_btn)

        # Results
        results_layout = QHBoxLayout()
        self.results_label = QLabel("RESULTS (0 found)")
        results_layout.addWidget(self.results_label)
        results_layout.addStretch()
        layout.addLayout(results_layout)

        self.results_list = QListWidget()
        self.results_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.results_list)

        # Info label
        self.info_label = QLabel("MULTI-SELECT: Metrics averaging only, not visual view")
        self.info_label.setStyleSheet("color: #808080;")
        layout.addWidget(self.info_label)

        # Buttons
        btn_layout = QHBoxLayout()
        self.compare_btn = QPushButton("COMPARE SELECTED")
        self.compare_btn.clicked.connect(self._compare)
        btn_layout.addWidget(self.compare_btn)

        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Base Directory", self._base_path
        )
        if path:
            self.path_edit.setText(path)

    def _scan(self):
        base_path = Path(self.path_edit.text())
        pattern = self.pattern_edit.text().strip()

        if not base_path.exists():
            return

        self._found_files.clear()
        self.results_list.clear()

        if not pattern:
            # Try to extract pattern from filename
            pattern = "*"

        # Convert glob pattern to regex for flexible matching
        regex_pattern = self._glob_to_regex(pattern)

        try:
            regex = re.compile(regex_pattern, re.IGNORECASE)
        except re.error:
            regex = None

        # Scan subdirectories
        for path in base_path.rglob("*"):
            if path.is_file() and path.suffix.lower() in ['.gif', '.png', '.jpg', '.jpeg']:
                if regex and regex.search(path.name):
                    self._found_files.append(path)
                elif not regex and pattern in path.name:
                    self._found_files.append(path)

        # Sort by path
        self._found_files.sort()

        # Update list
        for path in self._found_files:
            rel_path = path.relative_to(base_path) if path.is_relative_to(base_path) else path
            item = QListWidgetItem(str(rel_path))
            item.setData(Qt.UserRole, str(path))
            self.results_list.addItem(item)

        self.results_label.setText(f"RESULTS ({len(self._found_files)} found)")

    def _glob_to_regex(self, pattern: str) -> str:
        """Convert glob pattern to regex."""
        # Escape special regex characters except * and ?
        result = ""
        for char in pattern:
            if char == "*":
                result += ".*"
            elif char == "?":
                result += "."
            elif char in ".^$+{}[]|()":
                result += "\\" + char
            else:
                result += char
        return result

    def _compare(self):
        selected = self.results_list.selectedItems()
        if selected:
            paths = [item.data(Qt.UserRole) for item in selected]
            self.files_selected.emit(paths)
            self.accept()

    def set_pattern_from_file(self, filepath: str):
        """Extract pattern from a filename."""
        if not filepath:
            return

        path = Path(filepath)
        name = path.stem  # filename without extension
        ext = path.suffix

        # Try to find common patterns (numbers, etc.)
        # Replace trailing numbers with *
        pattern = re.sub(r'\d+$', '*', name)
        # Replace leading numbers with *
        pattern = re.sub(r'^\d+', '*', pattern)

        self.pattern_edit.setText(f"{pattern}{ext}")
        self.path_edit.setText(str(path.parent))

    def get_selected_paths(self) -> List[str]:
        """Get list of selected file paths."""
        selected = self.results_list.selectedItems()
        return [item.data(Qt.UserRole) for item in selected]
