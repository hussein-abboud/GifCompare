from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QPushButton, QLabel, QComboBox,
                             QFileDialog, QSplitter, QMessageBox, QProgressDialog,
                             QApplication)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from pathlib import Path
from typing import Optional, List
import numpy as np

from src.gif_handler import GifHandler
from src.overlay_engine import OverlayEngine, OverlayMode, GridOverlay
from src.metrics import MetricsCalculator, SequenceMetrics, average_sequence_metrics
from src.style import BRUTALIST_STYLE
from src.titles import get_random_title
from src.widgets.viewport import ViewportWidget
from src.widgets.playback import PlaybackControls, FrameSlider
from src.widgets.frame_strip import FrameStrip
from src.widgets.overlay_panel import OverlayModePanel, GridOverlayPanel
from src.widgets.metrics_tab import MetricsTab
from src.widgets.discovery import DiscoveryDialog


class GifCompareApp(QMainWindow):
    """Main application window for GIF comparison."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(get_random_title())
        self.setMinimumSize(1200, 800)

        # Core components
        self.gt_handler = GifHandler()
        self.pred_handler = GifHandler()
        self.overlay_engine = OverlayEngine()
        self.grid_overlay = GridOverlay()

        # State
        self._current_frame = 0
        self._updating = False
        self._flicker_timer = QTimer(self)
        self._flicker_timer.timeout.connect(self._on_flicker_tick)
        self._last_directory = str(Path.cwd())

        # Setup
        self.setStyleSheet(BRUTALIST_STYLE)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Top bar - file selection
        top_bar = self._create_top_bar()
        main_layout.addLayout(top_bar)

        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget, 1)

        # Visual tab
        visual_tab = QWidget()
        self.tab_widget.addTab(visual_tab, "VISUAL")
        self._setup_visual_tab(visual_tab)

        # Metrics tab
        self.metrics_tab = MetricsTab()
        self.tab_widget.addTab(self.metrics_tab, "METRICS")

    def _create_top_bar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(8)

        # Ground truth
        layout.addWidget(QLabel("GROUND TRUTH:"))
        self.gt_combo = QComboBox()
        self.gt_combo.setMinimumWidth(200)
        self.gt_combo.setEditable(True)
        layout.addWidget(self.gt_combo)

        self.gt_browse_btn = QPushButton("...")
        self.gt_browse_btn.setFixedWidth(30)
        self.gt_browse_btn.clicked.connect(lambda: self._browse_file("gt"))
        layout.addWidget(self.gt_browse_btn)

        layout.addSpacing(20)

        # Predicted
        layout.addWidget(QLabel("PREDICTED:"))
        self.pred_combo = QComboBox()
        self.pred_combo.setMinimumWidth(200)
        self.pred_combo.setEditable(True)
        layout.addWidget(self.pred_combo)

        self.pred_browse_btn = QPushButton("...")
        self.pred_browse_btn.setFixedWidth(30)
        self.pred_browse_btn.clicked.connect(lambda: self._browse_file("pred"))
        layout.addWidget(self.pred_browse_btn)

        layout.addStretch()

        # Discovery button
        self.discover_btn = QPushButton("DISCOVER IN PATH")
        self.discover_btn.clicked.connect(self._open_discovery)
        layout.addWidget(self.discover_btn)

        # Save button
        self.save_btn = QPushButton("SAVE OVERLAY")
        self.save_btn.clicked.connect(self._save_overlay)
        layout.addWidget(self.save_btn)

        return layout

    def _setup_visual_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Main splitter
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)

        # Top section - viewport and controls
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Viewport
        self.viewport_widget = ViewportWidget()
        top_layout.addWidget(self.viewport_widget, 1)

        # Playback controls
        playback_layout = QVBoxLayout()
        playback_layout.setSpacing(4)

        self.playback_controls = PlaybackControls()
        playback_layout.addWidget(self.playback_controls)

        self.frame_slider = FrameSlider()
        playback_layout.addWidget(self.frame_slider)

        top_layout.addLayout(playback_layout)

        # Overlay controls (horizontal)
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(16)

        self.overlay_panel = OverlayModePanel()
        controls_layout.addWidget(self.overlay_panel)

        self.grid_panel = GridOverlayPanel()
        controls_layout.addWidget(self.grid_panel)

        controls_layout.addStretch()

        top_layout.addLayout(controls_layout)

        splitter.addWidget(top_widget)

        # Bottom section - frame strips
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(4)

        self.gt_strip = FrameStrip("GROUND TRUTH FRAMES")
        bottom_layout.addWidget(self.gt_strip)

        self.pred_strip = FrameStrip("PREDICTED FRAMES")
        bottom_layout.addWidget(self.pred_strip)

        splitter.addWidget(bottom_widget)

        # Set splitter sizes
        splitter.setSizes([600, 200])

    def _connect_signals(self):
        # File selection
        self.gt_combo.currentTextChanged.connect(lambda p: self._load_file("gt", p))
        self.pred_combo.currentTextChanged.connect(lambda p: self._load_file("pred", p))

        # Playback
        self.playback_controls.frame_changed.connect(self._on_frame_changed)
        self.frame_slider.frame_changed.connect(self._on_frame_changed)

        # Frame strips
        self.gt_strip.frame_selected.connect(self._on_frame_changed)
        self.pred_strip.frame_selected.connect(self._on_frame_changed)
        self.gt_strip.frame_deleted.connect(lambda i: self._delete_frame("gt", i))
        self.pred_strip.frame_deleted.connect(lambda i: self._delete_frame("pred", i))
        self.gt_strip.frame_add_requested.connect(lambda i: self._add_frame("gt", i))
        self.pred_strip.frame_add_requested.connect(lambda i: self._add_frame("pred", i))

        # Overlay
        self.overlay_panel.mode_changed.connect(self._on_overlay_mode_changed)
        self.grid_panel.settings_changed.connect(self._update_display)

        # Metrics
        self.metrics_tab.calculate_btn.clicked.connect(self._calculate_metrics)

    def _browse_file(self, target: str):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Select {'Ground Truth' if target == 'gt' else 'Predicted'} GIF",
            self._last_directory,
            "GIF Files (*.gif);;All Files (*.*)"
        )
        if path:
            self._last_directory = str(Path(path).parent)
            combo = self.gt_combo if target == "gt" else self.pred_combo
            combo.setCurrentText(path)

    def _load_file(self, target: str, path: str):
        if not path or not Path(path).exists():
            return

        handler = self.gt_handler if target == "gt" else self.pred_handler
        if handler.load(path):
            self._update_after_load(target)

    def _update_after_load(self, target: str):
        handler = self.gt_handler if target == "gt" else self.pred_handler
        strip = self.gt_strip if target == "gt" else self.pred_strip

        # Update thumbnails
        thumbnails = []
        for i in range(handler.get_frame_count()):
            thumb = handler.get_thumbnail(i)
            if thumb is not None:
                thumbnails.append(thumb)
        strip.set_thumbnails(thumbnails)

        # Update playback controls with max frame count
        max_frames = max(self.gt_handler.get_frame_count(),
                        self.pred_handler.get_frame_count())
        self.playback_controls.set_frame_count(max_frames)
        self.frame_slider.set_frame_count(max_frames)

        # Set base interval from average duration
        if handler.get_frame_count() > 0:
            avg_duration = handler.get_average_duration()
            self.playback_controls.set_base_interval(avg_duration)

        # Update display
        self._update_display()

        # Fit to view
        self.viewport_widget.viewport.fit_in_view()

    def _on_frame_changed(self, frame: int):
        if self._updating:
            return
        self._updating = True
        try:
            self._current_frame = frame
            self.playback_controls.set_frame(frame, emit=False)
            self.frame_slider.set_frame(frame)
            self.gt_strip.set_selected(frame)
            self.pred_strip.set_selected(frame)
            self._update_display()
        finally:
            self._updating = False

    def _on_overlay_mode_changed(self, mode: OverlayMode):
        self.overlay_engine.set_mode(mode)

        # Handle flicker mode
        if mode == OverlayMode.FLICKER:
            self._flicker_timer.start(200)
        else:
            self._flicker_timer.stop()

        self._update_display()

    def _on_flicker_tick(self):
        self.overlay_engine.toggle_flicker()
        self._update_display()

    def _update_display(self):
        try:
            gt_frame = self.gt_handler.get_frame(self._current_frame)
            pred_frame = self.pred_handler.get_frame(self._current_frame)

            if gt_frame is None and pred_frame is None:
                return

            # Use whichever frame is available, or composite both
            if gt_frame is not None and pred_frame is not None:
                result = self.overlay_engine.composite(gt_frame, pred_frame)
            elif gt_frame is not None:
                result = gt_frame.copy()
            else:
                result = pred_frame.copy()

            # Apply grid overlay
            self.grid_overlay.set_enabled(self.grid_panel.is_enabled())
            self.grid_overlay.set_size(self.grid_panel.get_size())
            self.grid_overlay.set_color(self.grid_panel.get_color())
            self.grid_overlay.set_opacity(self.grid_panel.get_opacity())
            result = self.grid_overlay.apply(result)

            self.viewport_widget.set_image(result)
        except Exception as e:
            print(f"Display error: {e}")

    def _delete_frame(self, target: str, index: int):
        handler = self.gt_handler if target == "gt" else self.pred_handler
        if handler.delete_frame(index):
            self._update_after_load(target)

    def _add_frame(self, target: str, index: int):
        # Open file dialog to add frame
        path, _ = QFileDialog.getOpenFileName(
            self, "Add Frame",
            self._last_directory,
            "Image Files (*.png *.jpg *.gif);;All Files (*.*)"
        )
        if path:
            from PIL import Image
            img = Image.open(path).convert("RGBA")
            frame = np.array(img)

            handler = self.gt_handler if target == "gt" else self.pred_handler
            handler.insert_frame(index, frame)
            self._update_after_load(target)

    def _save_overlay(self):
        if self.gt_handler.get_frame_count() == 0 and self.pred_handler.get_frame_count() == 0:
            QMessageBox.warning(self, "Warning", "No frames loaded")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Overlay GIF",
            self._last_directory,
            "GIF Files (*.gif)"
        )
        if not path:
            return

        # Generate overlay frames
        max_frames = max(self.gt_handler.get_frame_count(),
                        self.pred_handler.get_frame_count())

        overlay_frames = []
        durations = []

        progress = QProgressDialog("Generating overlay...", "Cancel", 0, max_frames, self)
        progress.setWindowModality(Qt.WindowModal)

        for i in range(max_frames):
            if progress.wasCanceled():
                return
            progress.setValue(i)
            QApplication.processEvents()

            gt_frame = self.gt_handler.get_frame(i)
            pred_frame = self.pred_handler.get_frame(i)

            if gt_frame is not None and pred_frame is not None:
                result = self.overlay_engine.composite(gt_frame, pred_frame)
            elif gt_frame is not None:
                result = gt_frame.copy()
            else:
                result = pred_frame.copy()

            result = self.grid_overlay.apply(result)
            overlay_frames.append(result)
            durations.append(self.gt_handler.get_duration(i) or
                           self.pred_handler.get_duration(i) or 100)

        progress.close()

        # Save
        handler = GifHandler()
        if handler.save(path, overlay_frames, durations):
            QMessageBox.information(self, "Success", f"Saved to {path}")
        else:
            QMessageBox.warning(self, "Error", "Failed to save GIF")

    def _open_discovery(self):
        # Get current file path for pattern
        current_path = self.pred_combo.currentText() or self.gt_combo.currentText()

        dialog = DiscoveryDialog(self._last_directory, "", self)
        if current_path:
            dialog.set_pattern_from_file(current_path)

        dialog.files_selected.connect(self._on_discovery_selected)
        dialog.exec_()

    def _on_discovery_selected(self, paths: List[str]):
        if not paths:
            return

        if len(paths) == 1:
            # Single selection - load as predicted
            self.pred_combo.setCurrentText(paths[0])
        else:
            # Multiple selection - calculate averaged metrics
            self._calculate_averaged_metrics(paths)

    def _calculate_averaged_metrics(self, pred_paths: List[str]):
        if self.gt_handler.get_frame_count() == 0:
            QMessageBox.warning(self, "Warning", "Load ground truth first")
            return

        progress = QProgressDialog("Calculating metrics...", "Cancel",
                                  0, len(pred_paths), self)
        progress.setWindowModality(Qt.WindowModal)

        all_metrics: List[SequenceMetrics] = []
        calculator = MetricsCalculator()

        for i, path in enumerate(pred_paths):
            if progress.wasCanceled():
                return
            progress.setValue(i)
            QApplication.processEvents()

            pred = GifHandler()
            if pred.load(path):
                seq_metrics, _ = calculator.calculate_sequence_metrics(
                    self.gt_handler.frames, pred.frames
                )
                all_metrics.append(seq_metrics)

        progress.close()

        if all_metrics:
            averaged = average_sequence_metrics(all_metrics)
            self.metrics_tab.set_sequence_metrics(averaged)
            self.tab_widget.setCurrentWidget(self.metrics_tab)
            QMessageBox.information(
                self, "Averaged Metrics",
                f"Averaged metrics from {len(all_metrics)} files"
            )

    def _calculate_metrics(self):
        if self.gt_handler.get_frame_count() == 0:
            QMessageBox.warning(self, "Warning", "Load ground truth first")
            return
        if self.pred_handler.get_frame_count() == 0:
            QMessageBox.warning(self, "Warning", "Load predicted first")
            return

        progress = QProgressDialog("Calculating metrics...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        QApplication.processEvents()

        self.metrics_tab.calculate_metrics(
            self.gt_handler.frames,
            self.pred_handler.frames
        )

        progress.close()
