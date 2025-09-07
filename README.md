# D2R Loot Reader

**A Python library for parsing Diablo II: Resurrected item tooltips into structured JSON data.**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

D2R Loot Reader is a technical tool designed for developers, modders, and enthusiasts building applications for the Diablo II: Resurrected community. It uses advanced OCR (Optical Character Recognition) and fuzzy string matching to convert in-game item tooltips into machine-readable JSON format.

## 🎯 Use Cases

- **Loot Tracking Applications**: Build tools to track valuable drops and analyze loot statistics
- **Trading Platforms**: Create automated item cataloging for trading websites
- **Game Enhancement Tools**: Develop overlays or assistants that provide item information
- **Data Analysis**: Extract item data for statistical analysis and game research

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Tesseract OCR**: Install from [official Tesseract site](https://tesseract-ocr.github.io/tessdoc/Installation.html)

### Installation

```bash
pip install d2rlootreader
```

### Basic Usage

```python
from d2rlootreader.item_parser import ItemParser

# Parse tooltip text lines into structured JSON
lines = [
    "Rare Ring",
    "Required Level: 15", 
    "+25 to Life",
    "+15% Faster Cast Rate"
]

parser = ItemParser(lines)
item_data = parser.parse_item_lines_to_json()
print(item_data)
```

### CLI Commands

```bash
# Interactive screen capture and OCR parsing
d2rlootreader capture
```

## 📊 Output Format

The parser produces structured JSON following this schema:

```json
{
  "quality": "Unique|Set|Rare|Magic|Runeword|Base",
  "name": "Fortitude",
  "base": "Great Hauberk",
  "slot": "Body",
  "tier": "Elite",
  "requirements": {"strength": 118, "level": 59},
  "stats": {"defense": [1596]},
  "affixes": [
    ["#% Chance to cast level # [Skill] when struck", [20, 15, "Chilling Armor"]],
    ["+#% Faster Cast Rate", [25]],
    ["+#% Enhanced Damage", [300]],
    ["+#% Enhanced Defense", [215]],
    ["+# Defense", [15]],
    ["+# to Life (Based on Character Level)", [101]],
    ["Replenish Life +#", [7]],
    ["+#% to Maximum Lightning Resist", [5]],
    ["All Resistances +#", [29]],
    ["Damage Reduced by #", [7]],
    ["+#% Damage Taken Goes To Mana", [12]],
    ["+# to Light Radius", [1]],
    ["Increase Maximum Durability #%", [13]],
    ["Socketed (#)", [4]]
  ],
  "tooltip": ["Fortitude", "Great Hauberk", "'ElSolDolLo'", "Defense: 1596", ...]
}
```

## 🔧 Technical Architecture

### Core Components

- **OCR Engine**: Custom-trained Tesseract model optimized for D2R fonts
- **Fuzzy Matching**: RapidFuzz-powered intelligent text matching with typo tolerance
- **Image Processing**: OpenCV-based preprocessing for optimal OCR accuracy
- **Data Repository**: Comprehensive JSON databases of all D2R items, affixes, and skills

### Repository Files

The library includes extensive game data mappings:

- `affixes.json` - All possible item modifiers and their templates
- `bases.json` - Base item types with slots and tiers
- `uniques.json`, `set.json`, `runewords.json` - Named item databases
- `magic.json`, `rares.json` - Prefix/suffix combinations
- `skills.json`, `classes.json` - Character abilities and class restrictions
- `requirements.json`, `stats.json` - Item requirements and base statistics

### Intelligent Parsing Features

- **Template Matching**: Supports complex affix patterns like `"+# to # [Skill] ([Class] Only)"`
- **OCR Error Correction**: Handles common misreads (0→O, 1→l, 5→S, etc.)
- **Context-Aware Classification**: Distinguishes between item types using multiple signals
- **Fuzzy Thresholds**: Configurable matching sensitivity for various game data types

## 📸 Image Requirements

For optimal results, captured tooltip images should:

- **Start with item name** as the first line (crop out shop prices/vendor info)
- Have **clear, unobstructed text**
- Include the **complete tooltip** from name to last affix
- Use **game's default UI scaling** when possible

See example tooltip images in the `tests/tooltips/` directory.

## 🛠️ Advanced Usage

### Custom OCR Configuration

```python
from d2rlootreader.screen import capture_screen, preprocess
from d2rlootreader.item_parser import ItemParser
import pytesseract

# Capture and process with custom settings
image = capture_screen()
processed = preprocess(image, mode="adaptive")

# Extract text with custom OCR config
text = pytesseract.image_to_string(processed, lang="d2r", config="--psm 6")
lines = [line.strip() for line in text.splitlines() if line.strip()]

# Parse with debugging
parser = ItemParser(lines)
result = parser.parse_item_lines_to_json()
```

### Interactive Region Selection

```python
from d2rlootreader.region_selector import select_region

# Full-screen overlay for precise tooltip selection
selected_image = select_region()
```

### Batch Processing

```python
import glob
from pathlib import Path

# Process multiple tooltip images
for image_path in glob.glob("tooltips/*.png"):
    # Your processing logic here
    pass
```

## ⚠️ Current Limitations

This is an early-stage tool with known limitations:

- **Special Characters**: Some Unicode symbols may not parse correctly
- **Font Variations**: Works best with default game UI settings

Contributions and bug reports are welcome to improve parsing accuracy.

## 🧪 Development

### Setup Development Environment

```bash
git clone https://github.com/lucekdudek/d2r-loot-reader.git
cd d2r-loot-reader
pip install -e .[dev]
```

### Code Quality Tools

```bash
# Format code
black .
isort .

# Run tests
pytest tests/
```

### Testing with Sample Data

```bash
# Test with included tooltip samples
python -m pytest tests/test_item_parser.py -v
```

## 📝 Contributing

This project welcomes contributions from the D2R community:

- **Item Database Updates**: Add missing items, affixes, or skills
- **OCR Improvements**: Enhance text recognition accuracy
- **Parser Logic**: Handle edge cases and special item types
- **Documentation**: Improve guides and examples

## 📄 License

This project is licensed under the **GPL-3.0-or-later** license. See the [LICENSE](LICENSE) file for details.

### Third-Party Components

This project includes the custom Tesseract training data from the "horadricapp" project by stephaistos, licensed under the MIT License. The component is located in `third_party/horadricapp/` with full attribution and license details.
