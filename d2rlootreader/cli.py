import argparse
import os
import pathlib
import sys

import cv2
import pytesseract

from d2rlootreader.region_selector import select_region
from d2rlootreader.screen import preprocess

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
TESSDATA_DIR = PROJECT_ROOT / "third_party" / "horadricapp"
TESSERACT_BLACKLIST = "@#!$^&*_|=?><,;®‘"


def _ensure_output_directory(file_path: str):
    """
    Ensures that the directory for the given file path exists.
    """
    output_dir = os.path.dirname(file_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)


def _save_image(image, path: str):
    """
    Saves an image to the specified path and prints a success or error message.
    """
    if cv2.imwrite(path, image):
        print(f"Image saved to: {path}")
    else:
        print(f"Error: Failed to save image to {path}", file=sys.stderr)


def capture_save_command(args):
    """
    Handles the 'capture-save' CLI command.
    Allows the user to select a screen region, captures it, and saves it to a specified file.

    Args:
        args: An argparse.Namespace object containing the command-line arguments.
              Expected attributes: 'out' (str) - output path for the captured image.
    """
    print("Please select the region of the screen to capture.")
    captured_image = select_region()
    if captured_image is None or captured_image.size == 0:
        print("Selection canceled. Exiting.", file=sys.stderr)
        return
    print("Region selected and captured.")
    _ensure_output_directory(args.out)
    _save_image(captured_image, args.out)


def preprocess_file_command(args):
    """
    Handles the 'preprocess-file' CLI command.
    Reads an image from a specified input path, preprocesses it using the given mode,
    and saves the result to an output path.

    Args:
        args: An argparse.Namespace object containing the command-line arguments.
              Expected attributes:
              - 'input' (str): Input image path.
              - 'out' (str): Output path for the processed image.
              - 'mode' (str): Preprocessing mode (e.g., "none", "otsu", "adaptive").
    """
    input_path = args.input
    output_path = args.out
    mode = args.mode

    image = cv2.imread(input_path)
    if image is None or image.size == 0:
        print(f"Error: Could not read input image from {input_path}", file=sys.stderr)
        return

    processed_image = preprocess(image, mode=mode)
    _ensure_output_directory(output_path)
    _save_image(processed_image, output_path)


def capture_ocr_command(args):
    """
    Select a region, preprocess it, then run Tesseract OCR and print or save the text.
    """
    print("Please select the region of the screen to capture.")
    captured_image = select_region()
    if captured_image is None or captured_image.size == 0:
        print("Selection canceled or empty image.", file=sys.stderr)
        return
    _save_image(captured_image, "tmp/tmp-captured.png")

    # Preprocess using the same pipeline as preprocess-file
    processed = preprocess(captured_image, mode="none")
    _save_image(processed, "tmp/tmp-processed.png")

    # Convert to RGB for pytesseract (OpenCV uses BGR; grayscale needs expansion)
    if len(processed.shape) == 2:
        rgb = cv2.cvtColor(processed, cv2.COLOR_GRAY2RGB)
    else:
        rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)

    # Build Tesseract config
    cfg_parts = [
        f"--tessdata-dir {TESSDATA_DIR}",
        f"-c tessedit_char_blacklist={TESSERACT_BLACKLIST}",
    ]
    config_str = " ".join(cfg_parts)

    # Run OCR
    try:
        text = pytesseract.image_to_string(rgb, lang="d2r", config=config_str)
    except RuntimeError as e:
        print(f"Tesseract OCR failed: {e}", file=sys.stderr)
        return

    # Output text
    with open("tmp/tmp-text.log", "w", encoding="utf-8") as f:
        f.write(text)


def main():
    """
    Main entry point for the D2R Loot Reader CLI application.
    Parses command-line arguments and executes the corresponding command.
    """
    parser = argparse.ArgumentParser(description="D2R Loot Reader CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Capture-save subcommand
    capture_save_parser = subparsers.add_parser(
        "capture-save", help="Selects a screen region, captures it, and saves to a file."
    )
    capture_save_parser.add_argument(
        "--out", "-o", required=True, help="Output path for the captured image (e.g., tmp/crop.png)"
    )
    capture_save_parser.set_defaults(func=capture_save_command)

    # Preprocess-file subcommand
    preprocess_file_parser = subparsers.add_parser(
        "preprocess-file", help="Reads an image, preprocesses it, and saves the result."
    )
    preprocess_file_parser.add_argument("--input", "-i", required=True, help="Input image path (e.g., tmp/crop.png)")
    preprocess_file_parser.add_argument(
        "--out", "-o", required=True, help="Output path for the processed image (e.g., tmp/crop_adaptive.png)"
    )
    preprocess_file_parser.add_argument(
        "--mode",
        "-m",
        choices=["none", "otsu", "adaptive"],
        default="adaptive",
        help="Preprocessing mode (none, otsu, adaptive)",
    )
    preprocess_file_parser.set_defaults(func=preprocess_file_command)

    # Capture-ocr subcommand
    capture_ocr_parser = subparsers.add_parser(
        "capture-ocr", help="Selects a screen region, preprocesses it, and extracts text with Tesseract."
    )
    capture_ocr_parser.set_defaults(func=capture_ocr_command)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
