import numpy as np
from enum import Enum
from typing import Tuple, Optional


class OverlayMode(Enum):
    NORMAL = "normal"
    DUAL_COLOR = "dual_color"
    DIFFERENCE = "difference"
    SSIM_MAP = "ssim_map"
    BLEND = "blend"
    FLICKER = "flicker"
    CHECKERBOARD = "checkerboard"
    SIDE_BY_SIDE = "side_by_side"


class OverlayEngine:
    """Engine for compositing two frames with various overlay modes."""

    def __init__(self):
        self.mode = OverlayMode.SIDE_BY_SIDE
        self.flicker_state = False
        self.checker_size = 32
        self.grid_thickness = 1
        # Colors for dual-color mode (RGB)
        self.gt_color = (0, 255, 0)  # Green for ground truth
        self.pred_color = (255, 0, 255)  # Magenta for predicted

    def set_mode(self, mode: OverlayMode):
        """Set the overlay mode."""
        self.mode = mode

    def toggle_flicker(self):
        """Toggle flicker state for flicker mode."""
        self.flicker_state = not self.flicker_state

    def composite(self, gt_frame: np.ndarray, pred_frame: np.ndarray) -> np.ndarray:
        """Composite two frames based on current mode."""
        # Ensure both frames are same size and RGBA
        gt = self._ensure_rgba(gt_frame)
        pred = self._ensure_rgba(pred_frame)

        # Resize pred to match gt if needed
        if gt.shape != pred.shape:
            from PIL import Image
            pred_img = Image.fromarray(pred)
            pred_img = pred_img.resize((gt.shape[1], gt.shape[0]), Image.Resampling.LANCZOS)
            pred = np.array(pred_img)

        if self.mode == OverlayMode.NORMAL:
            return self._composite_normal(gt, pred)
        elif self.mode == OverlayMode.DUAL_COLOR:
            return self._composite_dual_color(gt, pred)
        elif self.mode == OverlayMode.DIFFERENCE:
            return self._composite_difference(gt, pred)
        elif self.mode == OverlayMode.SSIM_MAP:
            return self._composite_ssim_map(gt, pred)
        elif self.mode == OverlayMode.BLEND:
            return self._composite_blend(gt, pred)
        elif self.mode == OverlayMode.FLICKER:
            return self._composite_flicker(gt, pred)
        elif self.mode == OverlayMode.CHECKERBOARD:
            return self._composite_checkerboard(gt, pred)
        elif self.mode == OverlayMode.SIDE_BY_SIDE:
            return self._composite_side_by_side(gt, pred)
        return gt

    def _ensure_rgba(self, frame: np.ndarray) -> np.ndarray:
        """Ensure frame is RGBA format."""
        if frame.ndim == 2:
            # Grayscale to RGBA
            rgba = np.zeros((frame.shape[0], frame.shape[1], 4), dtype=np.uint8)
            rgba[:, :, 0] = frame
            rgba[:, :, 1] = frame
            rgba[:, :, 2] = frame
            rgba[:, :, 3] = 255
            return rgba
        elif frame.shape[-1] == 3:
            # RGB to RGBA
            rgba = np.zeros((frame.shape[0], frame.shape[1], 4), dtype=np.uint8)
            rgba[:, :, :3] = frame
            rgba[:, :, 3] = 255
            return rgba
        return frame.copy()

    def _composite_normal(self, gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
        """Show predicted on top of ground truth."""
        return pred.copy()

    def _composite_dual_color(self, gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
        """Tint ground truth and predicted with different colors."""
        # Convert to grayscale luminance
        gt_gray = 0.299 * gt[:, :, 0] + 0.587 * gt[:, :, 1] + 0.114 * gt[:, :, 2]
        pred_gray = 0.299 * pred[:, :, 0] + 0.587 * pred[:, :, 1] + 0.114 * pred[:, :, 2]

        result = np.zeros_like(gt)
        # Apply colors
        for i, c in enumerate(self.gt_color):
            result[:, :, i] = np.clip(result[:, :, i] + (gt_gray * c / 255), 0, 255)
        for i, c in enumerate(self.pred_color):
            result[:, :, i] = np.clip(result[:, :, i] + (pred_gray * c / 255), 0, 255)
        result[:, :, 3] = 255
        return result.astype(np.uint8)

    def _composite_difference(self, gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
        """Show difference heatmap between frames."""
        # Calculate absolute difference
        diff = np.abs(gt[:, :, :3].astype(np.float32) - pred[:, :, :3].astype(np.float32))
        diff_gray = np.mean(diff, axis=2)

        # Normalize to 0-1
        max_diff = diff_gray.max() if diff_gray.max() > 0 else 1
        diff_norm = diff_gray / max_diff

        # Apply heatmap colormap (blue -> green -> yellow -> red)
        result = np.zeros_like(gt)
        result[:, :, 0] = np.clip(diff_norm * 4 * 255, 0, 255)  # Red
        result[:, :, 1] = np.clip((1 - np.abs(diff_norm - 0.5) * 2) * 255, 0, 255)  # Green
        result[:, :, 2] = np.clip((1 - diff_norm) * 255, 0, 255)  # Blue
        result[:, :, 3] = 255
        return result.astype(np.uint8)

    def _composite_ssim_map(self, gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
        """Show local SSIM as heatmap. Green=similar, red=different."""
        from skimage.metrics import structural_similarity as ssim

        # Convert to grayscale
        gt_gray = (0.299 * gt[:, :, 0] + 0.587 * gt[:, :, 1] + 0.114 * gt[:, :, 2]).astype(np.uint8)
        pred_gray = (0.299 * pred[:, :, 0] + 0.587 * pred[:, :, 1] + 0.114 * pred[:, :, 2]).astype(np.uint8)

        # Compute SSIM with local map
        try:
            _, ssim_map = ssim(gt_gray, pred_gray, data_range=255, full=True)
        except Exception:
            # Fallback if SSIM fails
            return self._composite_difference(gt, pred)

        # ssim_map values are -1 to 1, normalize to 0-1
        ssim_norm = (ssim_map + 1) / 2
        ssim_norm = np.clip(ssim_norm, 0, 1)

        # Apply heatmap: green=1 (identical), red=0 (different)
        result = np.zeros_like(gt)
        result[:, :, 0] = ((1 - ssim_norm) * 255).astype(np.uint8)  # Red
        result[:, :, 1] = (ssim_norm * 255).astype(np.uint8)  # Green
        result[:, :, 2] = 0  # Blue
        result[:, :, 3] = 255
        return result

    def _composite_blend(self, gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
        """Blend both frames at 50% opacity each."""
        result = (gt.astype(np.float32) * 0.5 + pred.astype(np.float32) * 0.5)
        result[:, :, 3] = 255
        return result.astype(np.uint8)

    def _composite_flicker(self, gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
        """Alternate between frames (toggle with flicker_state)."""
        return gt.copy() if self.flicker_state else pred.copy()

    def _composite_checkerboard(self, gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
        """Show alternating checkerboard pattern of both frames with matching grid."""
        h, w = gt.shape[:2]
        result = np.zeros_like(gt)

        # Create checkerboard mask
        y_indices = np.arange(h) // self.checker_size
        x_indices = np.arange(w) // self.checker_size
        yy, xx = np.meshgrid(y_indices, x_indices, indexing='ij')
        mask = (yy + xx) % 2 == 0

        # Apply mask
        for c in range(4):
            result[:, :, c] = np.where(mask, gt[:, :, c], pred[:, :, c])

        # Draw grid lines matching checker size
        grid_color = np.array([80, 80, 80, 255], dtype=np.uint8)
        # Vertical lines
        for x in range(0, w, self.checker_size):
            x_end = min(x + self.grid_thickness, w)
            result[:, x:x_end, :] = grid_color
        # Horizontal lines
        for y in range(0, h, self.checker_size):
            y_end = min(y + self.grid_thickness, h)
            result[y:y_end, :, :] = grid_color

        # Mark predicted tiles with magenta dot in corner
        dot_size = max(3, self.checker_size // 10)
        magenta = np.array([255, 80, 255, 255], dtype=np.uint8)

        for ty in range(int(np.ceil(h / self.checker_size))):
            for tx in range(int(np.ceil(w / self.checker_size))):
                if (ty + tx) % 2 == 1:  # Predicted tile
                    # Draw dot in top-left corner of tile
                    y_start = ty * self.checker_size + 2
                    x_start = tx * self.checker_size + 2
                    y_end = min(y_start + dot_size, h)
                    x_end = min(x_start + dot_size, w)
                    if y_start < h and x_start < w:
                        result[y_start:y_end, x_start:x_end, :] = magenta

        return result

    def _composite_side_by_side(self, gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
        """Show ground truth and predicted side by side."""
        h, w = gt.shape[:2]
        # Create result with double width
        result = np.zeros((h, w * 2, 4), dtype=np.uint8)
        # Left side: ground truth
        result[:, :w, :] = gt
        # Right side: predicted
        result[:, w:, :] = pred
        return result


class GridOverlay:
    """Overlay a grid on top of an image."""

    def __init__(self):
        self.enabled = False
        self.size = 32
        self.color = (128, 128, 128)
        self.opacity = 0.5
        self.thickness = 1

    def apply(self, frame: np.ndarray) -> np.ndarray:
        """Apply grid overlay to frame."""
        if not self.enabled:
            return frame

        result = frame.copy().astype(np.float32)
        h, w = frame.shape[:2]
        alpha = self.opacity

        # Draw vertical lines
        for x in range(0, w, self.size):
            x_end = min(x + self.thickness, w)
            for c in range(3):
                result[:, x:x_end, c] = result[:, x:x_end, c] * (1 - alpha) + self.color[c] * alpha

        # Draw horizontal lines
        for y in range(0, h, self.size):
            y_end = min(y + self.thickness, h)
            for c in range(3):
                result[y:y_end, :, c] = result[y:y_end, :, c] * (1 - alpha) + self.color[c] * alpha

        return result.astype(np.uint8)

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def set_size(self, size: int):
        self.size = max(4, size)

    def set_color(self, color: Tuple[int, int, int]):
        self.color = color

    def set_opacity(self, opacity: float):
        self.opacity = max(0.0, min(1.0, opacity))

    def set_thickness(self, thickness: int):
        self.thickness = max(1, thickness)
