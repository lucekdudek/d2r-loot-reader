# Diablo II: Resurrected Loot Tooltip Reader

This is a command-line tool for Diablo II: Resurrected that helps with reading loot tooltips. It provides functionalities to capture a specific region of the screen, preprocess the captured image to enhance text readability, and display an overlay of the selected region for calibration.

2## Features
22
*   **Interactive Region Selection:** Easily select any part of the screen to capture.
*   **Image Preprocessing:** Enhance captured images for better text readability using various thresholding methods.
*   **ROI Overlay:** Display a transparent overlay of the selected region for easy calibration.
*   **Command-Line Interface:** All functionalities are accessible through a simple and intuitive CLI.

## How it Works

The tool is designed to streamline the process of extracting information from in-game tooltips. It operates through a series of commands:

1.  **`capture-save`**: The user selects a region of the screen where loot tooltips typically appear. The tool captures this region and saves it as an image file (e.g., `.png`). Simultaneously, it creates a JSON file containing the precise coordinates and dimensions of the captured region (Region of Interest or ROI).

2.  **`preprocess-file`**: The captured image is then processed to improve the quality and clarity of the text. This is a crucial step for preparing the image for Optical Character Recognition (OCR). The tool offers several preprocessing modes, such as adaptive thresholding, to handle different lighting conditions and backgrounds.

3.  **`overlay`**: To ensure that the capture region is correctly positioned, the tool can display a transparent overlay on the screen. This overlay visually represents the captured area, allowing the user to align it with the game's UI elements.

## Installation

1.  **Prerequisites**: Ensure you have Python 3.8 or higher installed on your system.

2.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/d2r-loot-reader.git
    cd d2r-loot-reader
    ```

3.  **Install dependencies**:
    ```bash
    pip install .
    ```

## Usage

The tool is operated via the command line and has three main subcommands: `capture-save`, `preprocess-file`, and `overlay`.

### `capture-save`

This command allows you to select a region of the screen, capture it, and save the image and its coordinates.

**Command:**
```bash
d2r-loot-reader capture-save --out samples/crop.png
```

**Execution:**
1.  A full-screen capture of your desktop will be displayed.
2.  Click and drag your mouse to draw a rectangle over the desired area.
3.  Press `ENTER` or `SPACE` to confirm the selection, or `C` to cancel.
4.  The captured image will be saved to the specified output path (e.g., `samples/crop.png`).
5.  The coordinates of the selected region (ROI) will be saved in a corresponding JSON file (e.g., `samples/crop.json`).

### `preprocess-file`

This command reads an image, applies a specified preprocessing mode, and saves the result.

**Command:**
```bash
d2r-loot-reader preprocess-file --input samples/crop.png --out samples/crop_preprocessed.png --mode adaptive
```

**Arguments:**
*   `--input`: Path to the input image file.
*   `--out`: Path to save the preprocessed image.
*   `--mode`: The preprocessing technique to apply. Options are:
    *   `adaptive`: Adaptive Gaussian thresholding, ideal for uneven lighting.
    *   `otsu`: Otsu's global thresholding, best for bimodal images.
    *   `none`: Converts the image to grayscale without any thresholding.

### `overlay`

This command displays a transparent overlay of the previously saved ROI on the screen.

**Command:**
```bash
d2r-loot-reader overlay --roi-file samples/crop.json
```

**Execution:**
1.  A transparent red rectangle will appear on the screen, outlining the ROI defined in the specified JSON file.
2.  This helps in verifying the position of the capture area.
3.  Press the `ESC` key to close the overlay.

## Dependencies

This tool relies on the following Python libraries:

*   **`mss`**: For efficient screen capturing.
*   **`opencv-python`**: For image processing and the ROI selection interface.
*   **`numpy`**: For numerical operations on image data.
*   **`PyQt5`**: For rendering the transparent overlay window.

## Future Work

The current version of the tool focuses on capturing and preparing the image. The next logical step is to integrate an OCR engine to extract the text from the preprocessed tooltips. Some potential libraries for this are:

*   **Tesseract (`pytesseract`)**: A powerful and popular OCR engine. It can be integrated by adding a new `ocr-file` command to the CLI, which would take a preprocessed image file and output the recognized text.
*   **EasyOCR**: A more modern and deep-learning-based OCR library. This could be an alternative to Tesseract, potentially offering better accuracy for in-game text.

By adding OCR capabilities, this tool can be extended to automatically read and log loot information, creating a comprehensive loot tracking system for Diablo II: Resurrected.