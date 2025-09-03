# Diablo II: Resurrected Loot Tooltip Reader

This project provides a tool to read and process loot tooltips from Diablo II: Resurrected.

## Features

* Captures in-game loot tooltips.
* Saves captured tooltips as image files.

## Installation

### Prerequisites

* Python 3.8 or higher.
* Tesseract OCR (Optical Character Recognition) engine must be installed and available in your system's PATH.

### Steps

1. **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/d2r-loot-reader.git
    cd d2r-loot-reader
    ```

2. **Create and activate a virtual environment (recommended):**

    ```bash
    python -m venv .venv
    # On Windows
    .venv\Scripts\activate
    # On macOS/Linux
    # source .venv/bin/activate
    ```

3. **Install dependencies:**

    ```bash
    pip install .
    ```

## Usage

### Running the application

The primary way to run the application is by executing the `d2rlootreader.bat` script.

```bash
.\d2rlootreader.bat
```

This script will activate the virtual environment, run the loot capture, and save the output to `tmp/temp.png`.

For silent execution (without a command prompt window), you can use `d2rlootreader.vbs`:

```bash
.\d2rlootreader.vbs
```

### Command Line Interface (CLI)

After installation, you can also use the `d2rlootreader` command directly from your activated virtual environment:

```bash
# To capture and save a tooltip to a specified file
d2rlootreader capture-save --o="tmp/output.png"
```

## Development

This project uses `black` for code formatting and `isort` for import sorting. You can install them via the `dev` optional dependency:

```bash
pip install .[dev]
```

Then, you can run them:

```bash
black .
isort .
```
