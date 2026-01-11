# GIF Compare

Brutalist GIF comparison tool for evaluating predicted outputs against ground truth.

## Features

- **Visual Comparison**: Side-by-side, blend, difference heatmap, dual-color, flicker, checkerboard overlays
- **Playback**: Frame-by-frame navigation, adjustable speed (0.01x - 8x)
- **Metrics**: PSNR, SSIM, MS-SSIM, LPIPS, MSE, MAE per-frame and averaged
- **Frame Editing**: Add/delete frames, export overlay as GIF
- **Batch Discovery**: Scan directories for similar files, multi-select for averaged metrics
- **Grid Overlay**: Configurable size, color, opacity

## Usage

```bash
python main.py
```

Load ground truth and predicted GIFs, compare visually or quantitatively.

## Requirements

- PyQt5
- numpy, pillow, imageio
- scikit-image, pytorch-msssim, lpips (for metrics)

## Controls

- **Zoom**: Mouse wheel or slider
- **Pan**: Right/middle mouse drag
- **Playback**: Space or play button
