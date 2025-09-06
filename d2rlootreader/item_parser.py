import json
from enum import Enum
from typing import Any, Dict, List, Tuple

from rapidfuzz import fuzz, process

from d2rlootreader.cfg import REPOSITORY_DIR

# match, score, idx = process.extractOne(query, choices, scorer=fuzz.ratio, score_cutoff=50)


class Q(Enum):
    UNKNOWN = "Unknown"
    BASE = "Base"
    MAGIC = "Magic"
    RARE = "Rare"
    SET = "Set"
    UNIQUE = "Unique"
    RUNEWORD = "Runeword"


class ItemParser:
    scorers = [fuzz.ratio, fuzz.partial_ratio]

    def __init__(self, lines: List[str]):
        self.R = self.repository_data = self.load_repository_data()
        self.lines = lines

    def load_repository_data(self) -> Dict[str, Any]:
        data = {}
        for fname in REPOSITORY_DIR.glob("*.json"):
            with open(fname, encoding="utf-8") as f:
                data[fname.stem] = json.load(f)
        return data

    def parse_item_lines_to_json(self) -> Dict[str, Any]:
        result = {
            "quality": None,
            "name": None,
            "base": None,
            "slot": None,
            "tier": None,
            "requirements": {},
            "stats": {},
            "affixes": {},
            "tooltip": self.lines,
        }
        
        result["quality"], result["name"] = self._parse_item_quality_n_name()
        result["base"], result["slot"], result["tier"] = self._parse_item_base_n_slot_n_tier(0 if result["quality"] in (Q.BASE.value, Q.MAGIC.value) else 1)
        if result["quality"] == Q.BASE.value:
            result["name"] = result["base"]


        return result

    def _parse_item_quality_n_name(self):
        name_line = self.lines[0].strip()

        match, _, _ = process.extractOne(
            name_line, self.R.get("runewords", {}).keys(), scorer=fuzz.ratio, score_cutoff=85
        ) or (None, 0, None)
        if match:
            return Q.RUNEWORD.value, match

        for scorer in self.scorers:
            match, _, _ = process.extractOne(
                name_line, self.R.get("uniques", {}).keys(), scorer=scorer, score_cutoff=85
            ) or (None, 0, None)
            if match:
                return Q.UNIQUE.value, match

        for scorer in self.scorers:
            match, _, _ = process.extractOne(
                name_line, self.R.get("set", {}).keys(), scorer=scorer, score_cutoff=85
            ) or (None, 0, None)
            if match:
                return Q.SET.value, match

        rares = self.R.get("rares", {})
        prefix, _, _ = process.extractOne(
            name_line, rares["prefixes"], scorer=fuzz.partial_ratio, score_cutoff=85
        ) or (None, 0, None)
        suffix, _, _ = process.extractOne(
            name_line, rares["suffixes"], scorer=fuzz.partial_ratio, score_cutoff=85
        ) or (None, 0, None)
        name = f"{prefix} {suffix}".strip()
        if name.lower() == name_line.lower():
            return Q.RARE.value, name

        magic = self.R.get("magic", {})
        prefix, _, _ = process.extractOne(
            name_line, magic["prefixes"], scorer=fuzz.partial_ratio, score_cutoff=85
        ) or (None, 0, None)
        suffix, _, _ = process.extractOne(
            name_line, magic["suffixes"], scorer=fuzz.partial_ratio, score_cutoff=85
        ) or (None, 0, None)
        name = f"{prefix} {suffix}".strip()
        if prefix and suffix:
            # TODO handle one affix magic items
            return Q.MAGIC.value, name

        return Q.BASE.value, None

    def _parse_item_base_n_slot_n_tier(self, line_idx):
        base_line = self.lines[line_idx].strip()
        bases = self.R.get("bases", {})

        for scorer in self.scorers:
            match, _, _ = process.extractOne(
                base_line, bases.keys(), scorer=scorer, score_cutoff=85
            ) or (None, 0, None)
            if match:
                return match, bases[match]["slot"], bases[match]["tier"]

        return None, None, None
