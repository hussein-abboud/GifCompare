import numpy as np
from PIL import Image
import imageio
from pathlib import Path
from typing import List, Tuple, Optional


class GifHandler:
    """Handles loading, manipulating, and saving GIF files."""

    def __init__(self):
        self.frames: List[np.ndarray] = []
        self.durations: List[int] = []
        self.path: Optional[Path] = None
        self.original_size: Tuple[int, int] = (0, 0)

    def load(self, path: str) -> bool:
        """Load a GIF file and extract all frames."""
        try:
            self.path = Path(path)
            self.frames = []
            self.durations = []

            # Use PIL for better duration handling
            pil_img = Image.open(path)
            self.original_size = pil_img.size

            try:
                while True:
                    # Convert to RGBA for consistent processing
                    frame = pil_img.convert("RGBA")
                    self.frames.append(np.array(frame))
                    # Get duration in ms, default to 100ms
                    duration = pil_img.info.get("duration", 100)
                    self.durations.append(duration)
                    pil_img.seek(pil_img.tell() + 1)
            except EOFError:
                pass

            return len(self.frames) > 0
        except Exception as e:
            print(f"Error loading GIF: {e}")
            return False

    def get_frame(self, index: int) -> Optional[np.ndarray]:
        """Get a specific frame by index."""
        if 0 <= index < len(self.frames):
            return self.frames[index]
        return None

    def get_frame_count(self) -> int:
        """Return total number of frames."""
        return len(self.frames)

    def get_duration(self, index: int) -> int:
        """Get duration of a specific frame in milliseconds."""
        if 0 <= index < len(self.durations):
            return self.durations[index]
        return 100

    def get_average_duration(self) -> int:
        """Get average frame duration."""
        if self.durations:
            return int(sum(self.durations) / len(self.durations))
        return 100

    def delete_frame(self, index: int) -> bool:
        """Delete a frame at the given index."""
        if 0 <= index < len(self.frames) and len(self.frames) > 1:
            del self.frames[index]
            del self.durations[index]
            return True
        return False

    def insert_frame(self, index: int, frame: np.ndarray, duration: int = 100) -> bool:
        """Insert a frame at the given index."""
        if 0 <= index <= len(self.frames):
            self.frames.insert(index, frame)
            self.durations.insert(index, duration)
            return True
        return False

    def add_frame(self, frame: np.ndarray, duration: int = 100):
        """Append a frame to the end."""
        self.frames.append(frame)
        self.durations.append(duration)

    def save(self, path: str, frames: Optional[List[np.ndarray]] = None,
             durations: Optional[List[int]] = None) -> bool:
        """Save frames as a GIF file."""
        try:
            save_frames = frames if frames is not None else self.frames
            save_durations = durations if durations is not None else self.durations

            if not save_frames:
                return False

            # Convert RGBA to RGB with white background for GIF
            rgb_frames = []
            for frame in save_frames:
                if frame.shape[-1] == 4:
                    # Composite over white background
                    rgb = np.zeros((frame.shape[0], frame.shape[1], 3), dtype=np.uint8)
                    alpha = frame[:, :, 3:4] / 255.0
                    rgb = (frame[:, :, :3] * alpha + 255 * (1 - alpha)).astype(np.uint8)
                    rgb_frames.append(rgb)
                else:
                    rgb_frames.append(frame[:, :, :3])

            # Calculate durations in seconds for imageio
            duration_sec = [d / 1000.0 for d in save_durations]

            imageio.mimsave(path, rgb_frames, duration=duration_sec, loop=0)
            return True
        except Exception as e:
            print(f"Error saving GIF: {e}")
            return False

    def get_size(self) -> Tuple[int, int]:
        """Return the size (width, height) of frames."""
        if self.frames:
            return (self.frames[0].shape[1], self.frames[0].shape[0])
        return self.original_size

    def resize_frames(self, target_size: Tuple[int, int]) -> List[np.ndarray]:
        """Resize all frames to target size."""
        resized = []
        for frame in self.frames:
            img = Image.fromarray(frame)
            img = img.resize(target_size, Image.Resampling.LANCZOS)
            resized.append(np.array(img))
        return resized

    def get_thumbnail(self, index: int, size: Tuple[int, int] = (64, 64)) -> Optional[np.ndarray]:
        """Get a thumbnail of a specific frame."""
        frame = self.get_frame(index)
        if frame is not None:
            img = Image.fromarray(frame)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            # Paste onto a fixed-size background
            thumb = Image.new("RGBA", size, (40, 40, 40, 255))
            offset = ((size[0] - img.width) // 2, (size[1] - img.height) // 2)
            thumb.paste(img, offset)
            return np.array(thumb)
        return None
