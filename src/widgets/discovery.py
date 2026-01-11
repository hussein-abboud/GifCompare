from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QListWidget, QListWidgetItem, QLabel,
                             QFileDialog, QAbstractItemView, QGroupBox, QProgressBar,
                             QApplication)
from PyQt5.QtCore import Qt, pyqtSignal
from pathlib import Path
from typing import List, Dict, Tuple


class DiscoveryDialog(QDialog):
    """Dialog for discovering folders containing matching filenames."""

    folder_selected = pyqtSignal(str, str)  # (gt_path, pred_path)
    folders_selected = pyqtSignal(list)  # List of (gt_path, pred_path) tuples for averaging

    def __init__(self, base_path: str, gt_name: str, pred_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DISCOVER MATCHING FOLDERS")
        self.setMinimumSize(600, 500)
        self._base_path = base_path or str(Path.cwd())
        self._gt_name = gt_name
        self._pred_name = pred_name
        self._found_folders: Dict[str, Tuple[Path, Path]] = {}  # folder -> (gt_path, pred_path)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Base path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("SCAN PATH:"))
        self.path_edit = QLineEdit(self._base_path)
        path_layout.addWidget(self.path_edit)
        self.browse_btn = QPushButton("...")
        self.browse_btn.setFixedWidth(30)
        self.browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(self.browse_btn)
        layout.addLayout(path_layout)

        # Target filenames
        files_group = QGroupBox("LOOKING FOR")
        files_layout = QVBoxLayout(files_group)

        gt_layout = QHBoxLayout()
        gt_layout.addWidget(QLabel("GT:"))
        self.gt_label = QLabel(self._gt_name or "(not set)")
        self.gt_label.setStyleSheet("color: #80ff80;")
        gt_layout.addWidget(self.gt_label)
        gt_layout.addStretch()
        files_layout.addLayout(gt_layout)

        pred_layout = QHBoxLayout()
        pred_layout.addWidget(QLabel("PRED:"))
        self.pred_label = QLabel(self._pred_name or "(not set)")
        self.pred_label.setStyleSheet("color: #ff80ff;")
        pred_layout.addWidget(self.pred_label)
        pred_layout.addStretch()
        files_layout.addLayout(pred_layout)

        layout.addWidget(files_group)

        # Scan button and progress bar
        scan_layout = QHBoxLayout()
        self.scan_btn = QPushButton("SCAN SUBFOLDERS")
        self.scan_btn.clicked.connect(self._scan)
        scan_layout.addWidget(self.scan_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.hide()
        scan_layout.addWidget(self.progress_bar)

        layout.addLayout(scan_layout)

        # Results
        results_layout = QHBoxLayout()
        self.results_label = QLabel("FOLDERS (0 found)")
        results_layout.addWidget(self.results_label)
        results_layout.addStretch()
        layout.addLayout(results_layout)

        self.results_list = QListWidget()
        self.results_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.results_list)

        # Info label
        self.info_label = QLabel("Single select: load for visual comparison | Multi-select: average metrics")
        self.info_label.setStyleSheet("color: #808080;")
        layout.addWidget(self.info_label)

        # Buttons
        btn_layout = QHBoxLayout()
        self.compare_btn = QPushButton("COMPARE SELECTED")
        self.compare_btn.clicked.connect(self._compare)
        btn_layout.addWidget(self.compare_btn)

        self.close_btn = QPushButton("CLOSE")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Base Directory", self._base_path
        )
        if path:
            self.path_edit.setText(path)

    def _scan(self):
        base_path = Path(self.path_edit.text())

        if not base_path.exists():
            return

        self._found_folders.clear()
        self.results_list.clear()

        if not self._gt_name and not self._pred_name:
            self.results_label.setText("FOLDERS (no filenames to search)")
            return

        # Show progress bar, disable button
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("SCANNING...")
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.progress_bar.show()
        QApplication.processEvents()

        # First collect all directories
        all_folders = []
        for folder in base_path.rglob("*"):
            if folder.is_dir():
                all_folders.append(folder)

        # Switch to determinate mode
        self.progress_bar.setRange(0, len(all_folders))

        # Scan all subdirectories
        for i, folder in enumerate(all_folders):
            self.progress_bar.setValue(i)
            if i % 10 == 0:  # Update UI every 10 folders
                QApplication.processEvents()

            gt_path = None
            pred_path = None

            # Check if folder contains the target files
            if self._gt_name:
                candidate = folder / self._gt_name
                if candidate.exists():
                    gt_path = candidate

            if self._pred_name:
                candidate = folder / self._pred_name
                if candidate.exists():
                    pred_path = candidate

            # Only include if at least one file found
            if gt_path or pred_path:
                rel_folder = folder.relative_to(base_path) if folder.is_relative_to(base_path) else folder
                self._found_folders[str(rel_folder)] = (gt_path, pred_path)

        # Hide progress bar, re-enable button
        self.progress_bar.hide()
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("SCAN SUBFOLDERS")

        # Sort and update list
        for folder_name in sorted(self._found_folders.keys()):
            gt_path, pred_path = self._found_folders[folder_name]

            # Show status
            status = ""
            if gt_path and pred_path:
                status = "[GT+PRED]"
            elif gt_path:
                status = "[GT only]"
            else:
                status = "[PRED only]"

            item = QListWidgetItem(f"{status} {folder_name}")
            item.setData(Qt.UserRole, folder_name)
            self.results_list.addItem(item)

        self.results_label.setText(f"FOLDERS ({len(self._found_folders)} found)")

    def _compare(self):
        selected = self.results_list.selectedItems()
        if not selected:
            return

        if len(selected) == 1:
            # Single selection - load for visual comparison
            folder_name = selected[0].data(Qt.UserRole)
            gt_path, pred_path = self._found_folders[folder_name]
            self.folder_selected.emit(
                str(gt_path) if gt_path else "",
                str(pred_path) if pred_path else ""
            )
        else:
            # Multiple selection - for averaging metrics
            pairs = []
            for item in selected:
                folder_name = item.data(Qt.UserRole)
                gt_path, pred_path = self._found_folders[folder_name]
                if gt_path and pred_path:
                    pairs.append((str(gt_path), str(pred_path)))
            self.folders_selected.emit(pairs)

    def set_filenames(self, gt_name: str, pred_name: str):
        """Set the filenames to search for."""
        self._gt_name = gt_name
        self._pred_name = pred_name
        self.gt_label.setText(gt_name or "(not set)")
        self.pred_label.setText(pred_name or "(not set)")
