from typing import Literal

import cv2
import mss
import numpy as np

ADAPTIVE_THRESHOLD_BLOCK_SIZE = 21


def capture_screen():
    """
    Captures the entire screen using mss.

    Returns:
        numpy.ndarray: The captured image in BGR format.
    """
    with mss.mss() as sct:
        monitor = sct.monitors[0]  # Capture the primary monitor
        sct_img = sct.grab(monitor)
        # Convert to numpy array and then to BGR format for OpenCV
        img = np.array(sct_img)
        return img[:, :, :3]  # Convert BGRA to BGR


def capture_region(sct_instance, region):
    """
    Captures a specific region of the screen using a given mss instance.

    This function does not create any windows and returns the image data directly.

    Args:
        sct_instance (mss.mss): An active mss instance.
        region (dict): The screen region to capture, with 'left', 'top',
                       'width', and 'height'.

    Returns:
        numpy.ndarray: The captured image in BGR format.
    """
    screenshot = sct_instance.grab(region)
    return np.array(screenshot)[:, :, :3]  # Convert BGRA -> BGR


def preprocess(image_bgr: np.ndarray, mode: Literal["otsu", "adaptive", "none"] = "adaptive") -> np.ndarray:
    """
    Converts a BGR image to grayscale and applies thresholding based on the specified mode.

    Args:
        image_bgr (np.ndarray): The input image in BGR format.
        mode (Literal["otsu", "adaptive", "none"]): The thresholding mode to use.
            - "otsu": Uses Otsu's global thresholding. Best for images with a bimodal
                      histogram (e.g., clear foreground/background separation).
            - "adaptive": Uses adaptive Gaussian thresholding. Recommended for images
                          with uneven illumination or varying background intensity.
            - "none": Returns the grayscale image without thresholding.

    Returns:
        np.ndarray: A single-channel uint8 binary image (0 or 255) for "otsu" and
                    "adaptive" modes, or a single-channel uint8 grayscale image for
                    "none" mode.

    Raises:
        ValueError: If `blockSize` is not an odd integer >= 3 for "adaptive" mode.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    if mode == "otsu":
        _, binarized = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binarized
    elif mode == "adaptive":
        # Validate blockSize
        if not (
            isinstance(ADAPTIVE_THRESHOLD_BLOCK_SIZE, int)
            and ADAPTIVE_THRESHOLD_BLOCK_SIZE >= 3
            and ADAPTIVE_THRESHOLD_BLOCK_SIZE % 2 == 1
        ):
            raise ValueError("blockSize must be an odd integer >= 3 for adaptive thresholding.")
        binarized = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=ADAPTIVE_THRESHOLD_BLOCK_SIZE,
            C=5,
        )
        return binarized
    elif mode == "none":
        return gray.astype(np.uint8)
    else:
        raise ValueError(f"Invalid mode: {mode}. Expected 'otsu', 'adaptive', or 'none'.")
