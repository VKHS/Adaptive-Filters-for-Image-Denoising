"""Loading the test image.

The scripts look for ``data/lena.png`` (or another common Lena file name) and use it when it is present.
Otherwise they use ``data/camera.png``. Every image is converted to grayscale (ITU-R BT.601 luma, the same
weights as MATLAB's ``rgb2gray``), resized to 512 x 512 if needed and scaled to float64 in [0, 1].
"""
from pathlib import Path

import numpy as np
from skimage import io as skio
from skimage.transform import resize

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
PREFERRED = ["lena.png", "lena.tif", "lena.tiff", "lena.bmp", "lena.jpg", "lenna.png", "Lenna.png", "lena512.bmp"]
FALLBACK = "camera.png"


def find_test_image():
    """Return the path of the image the scripts will use."""
    for name in PREFERRED:
        p = DATA / name
        if p.exists():
            return p
    return DATA / FALLBACK


def to_gray(img):
    """RGB(A) or gray array -> gray float64 in [0, 1] (BT.601 weights 0.2989, 0.5870, 0.1140)."""
    img = np.asarray(img)
    if img.dtype == np.uint8:
        img = img.astype(np.float64) / 255.0
    elif img.dtype == np.uint16:
        img = img.astype(np.float64) / 65535.0
    else:
        img = img.astype(np.float64)
        if img.max() > 1.0:
            img = img / 255.0
    if img.ndim == 3:
        img = img[..., :3] @ np.array([0.2989, 0.5870, 0.1140])
    return img


def load_test_image(path=None, size=512):
    """Load the test image as a ``size`` x ``size`` float64 array in [0, 1]."""
    path = Path(path) if path is not None else find_test_image()
    img = to_gray(skio.imread(path))
    if img.shape != (size, size):
        img = resize(img, (size, size), order=3, anti_aliasing=True, preserve_range=True)
    return np.clip(img, 0.0, 1.0), path.stem
