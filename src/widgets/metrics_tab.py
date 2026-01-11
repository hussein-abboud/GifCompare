from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QGroupBox, QLabel, QPushButton,
                             QCheckBox, QHeaderView, QFileDialog, QProgressDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QPainter, QPen, QColor
import numpy as np
from typing import List, Optional
import json
import csv

from src.metrics import MetricsCalculator, FrameMetrics, SequenceMetrics


class MetricsGraph(QWidget):
    """Simple line graph for metrics visualization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}  # metric_name -> list of values
        self._visible = set()  # visible metric names
        self._colors = {
            "psnr": QColor(255, 100, 100),
            "ssim": QColor(100, 255, 100),
            "ms_ssim": QColor(100, 100, 255),
            "lpips": QColor(255, 255, 100),
            "mse": QColor(255, 100, 255),
            "mae": QColor(100, 255, 255),
        }
        self.setMinimumHeight(150)

    def set_data(self, metric_name: str, values: List[float]):
        """Set data for a metric."""
        self._data[metric_name] = values
        self.update()

    def set_visible(self, metric_name: str, visible: bool):
        """Set visibility of a metric."""
        if visible:
            self._visible.add(metric_name)
        else:
            self._visible.discard(metric_name)
        self.update()

    def clear(self):
        """Clear all data."""
        self._data.clear()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(26, 26, 26))

        # Border
        painter.setPen(QPen(QColor(64, 64, 64), 1))
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

        if not self._data or not self._visible:
            painter.setPen(QColor(128, 128, 128))
            painter.drawText(self.rect(), Qt.AlignCenter, "No data")
            return

        # Margins
        margin = 40
        graph_width = self.width() - 2 * margin
        graph_height = self.height() - 2 * margin

        if graph_width <= 0 or graph_height <= 0:
            return

        # Find global min/max for normalization
        all_values = []
        for name in self._visible:
            if name in self._data:
                all_values.extend(self._data[name])

        if not all_values:
            return

        min_val = min(all_values)
        max_val = max(all_values)
        if max_val == min_val:
            max_val = min_val + 1

        # Draw axes
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawLine(margin, margin, margin, self.height() - margin)
        painter.drawLine(margin, self.height() - margin,
                        self.width() - margin, self.height() - margin)

        # Draw each visible metric
        for name in self._visible:
            if name not in self._data:
                continue

            values = self._data[name]
            if not values:
                continue

            color = self._colors.get(name, QColor(200, 200, 200))
            painter.setPen(QPen(color, 2))

            points = []
            for i, val in enumerate(values):
                x = margin + (i / max(1, len(values) - 1)) * graph_width
                y = self.height() - margin - ((val - min_val) / (max_val - min_val)) * graph_height
                points.append((int(x), int(y)))

            for i in range(len(points) - 1):
                painter.drawLine(points[i][0], points[i][1],
                               points[i + 1][0], points[i + 1][1])


class MetricsTab(QWidget):
    """Tab for displaying metrics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._calculator = MetricsCalculator()
        self._frame_metrics: List[FrameMetrics] = []
        self._sequence_metrics: Optional[SequenceMetrics] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Sequence metrics
        seq_group = QGroupBox("SEQUENCE METRICS (AVERAGE)")
        seq_layout = QHBoxLayout(seq_group)

        self.psnr_label = QLabel("PSNR: --")
        self.ssim_label = QLabel("SSIM: --")
        self.ms_ssim_label = QLabel("MS-SSIM: --")
        self.lpips_label = QLabel("LPIPS: --")
        self.mse_label = QLabel("MSE: --")
        self.mae_label = QLabel("MAE: --")

        for label in [self.psnr_label, self.ssim_label, self.ms_ssim_label,
                      self.lpips_label, self.mse_label, self.mae_label]:
            label.setStyleSheet("font-family: monospace; padding: 8px;")
            seq_layout.addWidget(label)

        layout.addWidget(seq_group)

        # Per-frame metrics table
        table_group = QGroupBox("PER-FRAME METRICS")
        table_layout = QVBoxLayout(table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["FRAME", "PSNR", "SSIM", "MS-SSIM", "LPIPS", "MSE", "MAE"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { alternate-background-color: #252525; }
        """)
        table_layout.addWidget(self.table)

        layout.addWidget(table_group)

        # Graph
        graph_group = QGroupBox("METRIC GRAPH")
        graph_layout = QVBoxLayout(graph_group)

        self.graph = MetricsGraph()
        graph_layout.addWidget(self.graph)

        # Metric visibility checkboxes
        check_layout = QHBoxLayout()
        check_layout.addWidget(QLabel("SHOW:"))

        self._metric_checks = {}
        for name in ["psnr", "ssim", "ms_ssim", "lpips", "mse", "mae"]:
            check = QCheckBox(name.upper())
            check.setChecked(name in ["psnr", "ssim"])
            check.stateChanged.connect(lambda state, n=name: self._on_check_changed(n, state))
            self._metric_checks[name] = check
            check_layout.addWidget(check)

        check_layout.addStretch()
        graph_layout.addLayout(check_layout)

        layout.addWidget(graph_group)

        # Export buttons
        export_layout = QHBoxLayout()
        self.export_csv_btn = QPushButton("EXPORT CSV")
        self.export_csv_btn.clicked.connect(self._export_csv)
        export_layout.addWidget(self.export_csv_btn)

        self.export_json_btn = QPushButton("EXPORT JSON")
        self.export_json_btn.clicked.connect(self._export_json)
        export_layout.addWidget(self.export_json_btn)

        export_layout.addStretch()

        self.calculate_btn = QPushButton("CALCULATE METRICS")
        self.calculate_btn.clicked.connect(self._request_calculate)
        export_layout.addWidget(self.calculate_btn)

        layout.addLayout(export_layout)

        # Initialize graph visibility
        self.graph.set_visible("psnr", True)
        self.graph.set_visible("ssim", True)

    def _on_check_changed(self, name: str, state: int):
        self.graph.set_visible(name, state == Qt.Checked)

    def _request_calculate(self):
        # This will be connected by the main app
        pass

    def calculate_metrics(self, gt_frames: List[np.ndarray], pred_frames: List[np.ndarray]):
        """Calculate metrics for given frames."""
        self._sequence_metrics, self._frame_metrics = \
            self._calculator.calculate_sequence_metrics(gt_frames, pred_frames)
        self._update_display()

    def _update_display(self):
        """Update UI with calculated metrics."""
        if self._sequence_metrics:
            self.psnr_label.setText(f"PSNR: {self._sequence_metrics.psnr:.2f} dB")
            self.ssim_label.setText(f"SSIM: {self._sequence_metrics.ssim:.4f}")
            self.ms_ssim_label.setText(f"MS-SSIM: {self._sequence_metrics.ms_ssim:.4f}")
            self.lpips_label.setText(f"LPIPS: {self._sequence_metrics.lpips:.4f}")
            self.mse_label.setText(f"MSE: {self._sequence_metrics.mse:.6f}")
            self.mae_label.setText(f"MAE: {self._sequence_metrics.mae:.6f}")

        # Update table
        self.table.setRowCount(len(self._frame_metrics))
        for i, fm in enumerate(self._frame_metrics):
            self.table.setItem(i, 0, QTableWidgetItem(f"{fm.frame_index:04d}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"{fm.psnr:.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{fm.ssim:.4f}"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{fm.ms_ssim:.4f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{fm.lpips:.4f}"))
            self.table.setItem(i, 5, QTableWidgetItem(f"{fm.mse:.6f}"))
            self.table.setItem(i, 6, QTableWidgetItem(f"{fm.mae:.6f}"))

        # Update graph
        self.graph.clear()
        if self._frame_metrics:
            self.graph.set_data("psnr", [m.psnr for m in self._frame_metrics])
            self.graph.set_data("ssim", [m.ssim for m in self._frame_metrics])
            self.graph.set_data("ms_ssim", [m.ms_ssim for m in self._frame_metrics])
            self.graph.set_data("lpips", [m.lpips for m in self._frame_metrics])
            self.graph.set_data("mse", [m.mse for m in self._frame_metrics])
            self.graph.set_data("mae", [m.mae for m in self._frame_metrics])

    def set_sequence_metrics(self, metrics: SequenceMetrics):
        """Set sequence metrics directly (for averaging)."""
        self._sequence_metrics = metrics
        self.psnr_label.setText(f"PSNR: {metrics.psnr:.2f} dB")
        self.ssim_label.setText(f"SSIM: {metrics.ssim:.4f}")
        self.ms_ssim_label.setText(f"MS-SSIM: {metrics.ms_ssim:.4f}")
        self.lpips_label.setText(f"LPIPS: {metrics.lpips:.4f}")
        self.mse_label.setText(f"MSE: {metrics.mse:.6f}")
        self.mae_label.setText(f"MAE: {metrics.mae:.6f}")

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "", "CSV Files (*.csv)"
        )
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["frame", "psnr", "ssim", "ms_ssim", "lpips", "mse", "mae"])
                for fm in self._frame_metrics:
                    writer.writerow([
                        fm.frame_index, fm.psnr, fm.ssim, fm.ms_ssim,
                        fm.lpips, fm.mse, fm.mae
                    ])

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", "", "JSON Files (*.json)"
        )
        if path:
            data = {
                "sequence": {
                    "psnr": self._sequence_metrics.psnr if self._sequence_metrics else 0,
                    "ssim": self._sequence_metrics.ssim if self._sequence_metrics else 0,
                    "ms_ssim": self._sequence_metrics.ms_ssim if self._sequence_metrics else 0,
                    "lpips": self._sequence_metrics.lpips if self._sequence_metrics else 0,
                    "mse": self._sequence_metrics.mse if self._sequence_metrics else 0,
                    "mae": self._sequence_metrics.mae if self._sequence_metrics else 0,
                    "frame_count": self._sequence_metrics.frame_count if self._sequence_metrics else 0,
                },
                "frames": [
                    {
                        "frame": fm.frame_index,
                        "psnr": fm.psnr,
                        "ssim": fm.ssim,
                        "ms_ssim": fm.ms_ssim,
                        "lpips": fm.lpips,
                        "mse": fm.mse,
                        "mae": fm.mae,
                    }
                    for fm in self._frame_metrics
                ]
            }
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

    def clear(self):
        """Clear all metrics."""
        self._frame_metrics = []
        self._sequence_metrics = None
        self.table.setRowCount(0)
        self.graph.clear()
        for label in [self.psnr_label, self.ssim_label, self.ms_ssim_label,
                      self.lpips_label, self.mse_label, self.mae_label]:
            label.setText(label.text().split(":")[0] + ": --")
