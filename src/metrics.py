import numpy as np
import warnings
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr


@dataclass
class FrameMetrics:
    """Metrics for a single frame."""
    frame_index: int
    psnr: float
    ssim: float
    ms_ssim: float
    lpips: float
    mse: float
    mae: float


@dataclass
class SequenceMetrics:
    """Aggregated metrics for entire sequence."""
    psnr: float
    ssim: float
    ms_ssim: float
    lpips: float
    mse: float
    mae: float
    frame_count: int


class MetricsCalculator:
    """Calculate image quality metrics between ground truth and predicted frames."""

    def __init__(self):
        self._lpips_model = None
        self._device = None

    def _get_lpips_model(self):
        """Lazy load LPIPS model."""
        if self._lpips_model is None:
            try:
                import torch
                import lpips
                # Suppress deprecation warnings from torchvision/lpips
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning)
                    warnings.filterwarnings("ignore", category=FutureWarning)
                    self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                    self._lpips_model = lpips.LPIPS(net='alex', verbose=False).to(self._device)
                    self._lpips_model.eval()
            except Exception as e:
                print(f"Could not load LPIPS model: {e}")
                return None
        return self._lpips_model

    def _to_grayscale(self, img: np.ndarray) -> np.ndarray:
        """Convert image to grayscale."""
        if img.ndim == 2:
            return img
        if img.shape[-1] == 4:
            img = img[:, :, :3]
        return (0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]).astype(np.uint8)

    def _to_rgb(self, img: np.ndarray) -> np.ndarray:
        """Ensure image is RGB."""
        if img.ndim == 2:
            return np.stack([img, img, img], axis=-1)
        if img.shape[-1] == 4:
            return img[:, :, :3]
        return img

    def calculate_psnr(self, gt: np.ndarray, pred: np.ndarray) -> float:
        """Calculate Peak Signal-to-Noise Ratio."""
        try:
            gt_rgb = self._to_rgb(gt)
            pred_rgb = self._to_rgb(pred)
            return float(psnr(gt_rgb, pred_rgb, data_range=255))
        except Exception:
            return 0.0

    def calculate_ssim(self, gt: np.ndarray, pred: np.ndarray) -> float:
        """Calculate Structural Similarity Index."""
        try:
            gt_gray = self._to_grayscale(gt)
            pred_gray = self._to_grayscale(pred)
            return float(ssim(gt_gray, pred_gray, data_range=255))
        except Exception:
            return 0.0

    def calculate_ms_ssim(self, gt: np.ndarray, pred: np.ndarray) -> float:
        """Calculate Multi-Scale Structural Similarity Index."""
        try:
            import torch
            from pytorch_msssim import ms_ssim

            gt_rgb = self._to_rgb(gt).astype(np.float32) / 255.0
            pred_rgb = self._to_rgb(pred).astype(np.float32) / 255.0

            # Convert to torch tensors (B, C, H, W)
            gt_t = torch.from_numpy(gt_rgb).permute(2, 0, 1).unsqueeze(0)
            pred_t = torch.from_numpy(pred_rgb).permute(2, 0, 1).unsqueeze(0)

            # MS-SSIM requires minimum size
            min_dim = min(gt_t.shape[2], gt_t.shape[3])
            if min_dim < 160:
                # Fall back to regular SSIM for small images
                return self.calculate_ssim(gt, pred)

            return float(ms_ssim(gt_t, pred_t, data_range=1.0))
        except Exception:
            return self.calculate_ssim(gt, pred)

    def calculate_lpips(self, gt: np.ndarray, pred: np.ndarray) -> float:
        """Calculate Learned Perceptual Image Patch Similarity."""
        try:
            import torch

            model = self._get_lpips_model()
            if model is None:
                return 0.0

            gt_rgb = self._to_rgb(gt).astype(np.float32) / 255.0
            pred_rgb = self._to_rgb(pred).astype(np.float32) / 255.0

            # Normalize to [-1, 1]
            gt_rgb = gt_rgb * 2 - 1
            pred_rgb = pred_rgb * 2 - 1

            # Convert to torch tensors (B, C, H, W)
            gt_t = torch.from_numpy(gt_rgb).permute(2, 0, 1).unsqueeze(0).float().to(self._device)
            pred_t = torch.from_numpy(pred_rgb).permute(2, 0, 1).unsqueeze(0).float().to(self._device)

            with torch.no_grad():
                result = model(gt_t, pred_t)
            return float(result.item())
        except Exception:
            return 0.0

    def calculate_mse(self, gt: np.ndarray, pred: np.ndarray) -> float:
        """Calculate Mean Squared Error."""
        try:
            gt_rgb = self._to_rgb(gt).astype(np.float32) / 255.0
            pred_rgb = self._to_rgb(pred).astype(np.float32) / 255.0
            return float(np.mean((gt_rgb - pred_rgb) ** 2))
        except Exception:
            return 0.0

    def calculate_mae(self, gt: np.ndarray, pred: np.ndarray) -> float:
        """Calculate Mean Absolute Error."""
        try:
            gt_rgb = self._to_rgb(gt).astype(np.float32) / 255.0
            pred_rgb = self._to_rgb(pred).astype(np.float32) / 255.0
            return float(np.mean(np.abs(gt_rgb - pred_rgb)))
        except Exception:
            return 0.0

    def calculate_frame_metrics(self, gt: np.ndarray, pred: np.ndarray,
                                 frame_index: int) -> FrameMetrics:
        """Calculate all metrics for a single frame pair."""
        return FrameMetrics(
            frame_index=frame_index,
            psnr=self.calculate_psnr(gt, pred),
            ssim=self.calculate_ssim(gt, pred),
            ms_ssim=self.calculate_ms_ssim(gt, pred),
            lpips=self.calculate_lpips(gt, pred),
            mse=self.calculate_mse(gt, pred),
            mae=self.calculate_mae(gt, pred)
        )

    def calculate_sequence_metrics(self, gt_frames: List[np.ndarray],
                                    pred_frames: List[np.ndarray]) -> Tuple[SequenceMetrics, List[FrameMetrics]]:
        """Calculate metrics for entire sequence."""
        frame_metrics = []
        min_frames = min(len(gt_frames), len(pred_frames))

        for i in range(min_frames):
            metrics = self.calculate_frame_metrics(gt_frames[i], pred_frames[i], i)
            frame_metrics.append(metrics)

        if not frame_metrics:
            return SequenceMetrics(0, 0, 0, 0, 0, 0, 0), []

        # Average metrics
        seq_metrics = SequenceMetrics(
            psnr=np.mean([m.psnr for m in frame_metrics]),
            ssim=np.mean([m.ssim for m in frame_metrics]),
            ms_ssim=np.mean([m.ms_ssim for m in frame_metrics]),
            lpips=np.mean([m.lpips for m in frame_metrics]),
            mse=np.mean([m.mse for m in frame_metrics]),
            mae=np.mean([m.mae for m in frame_metrics]),
            frame_count=min_frames
        )

        return seq_metrics, frame_metrics


def average_sequence_metrics(metrics_list: List[SequenceMetrics]) -> SequenceMetrics:
    """Average multiple sequence metrics (for multi-select comparison)."""
    if not metrics_list:
        return SequenceMetrics(0, 0, 0, 0, 0, 0, 0)

    return SequenceMetrics(
        psnr=np.mean([m.psnr for m in metrics_list]),
        ssim=np.mean([m.ssim for m in metrics_list]),
        ms_ssim=np.mean([m.ms_ssim for m in metrics_list]),
        lpips=np.mean([m.lpips for m in metrics_list]),
        mse=np.mean([m.mse for m in metrics_list]),
        mae=np.mean([m.mae for m in metrics_list]),
        frame_count=int(np.mean([m.frame_count for m in metrics_list]))
    )
