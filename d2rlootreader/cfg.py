import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_DIR = PROJECT_ROOT / "d2rlootreader" / "repository"

TESSDATA_DIR = PROJECT_ROOT / "third_party" / "horadricapp"
TESSERACT_BLACKLIST = "@#!$^&*_|=?><,;®‘"

TMP_DIR = Path(os.environ.get("D2R_LOOT_READER_TMP", PROJECT_ROOT / "tmp"))
