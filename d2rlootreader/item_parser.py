import json
import re
from enum import Enum
from typing import Any, Dict, Final, List

from rapidfuzz import fuzz, process

from d2rlootreader.cfg import REPOSITORY_DIR


class Q(Enum):
    UNKNOWN = "Unknown"
    BASE = "Base"
    MAGIC = "Magic"
    RARE = "Rare"
    SET = "Set"
    UNIQUE = "Unique"
    RUNEWORD = "Runeword"


class ItemParser:
    _none_match: Final = (None, 0, None)
    _scorers: Final = [fuzz.ratio, fuzz.token_set_ratio]
    _num_like: Final = r"(?i)\b(?:\d|[OIlZSBgq])+\b"
    _digit_translation: Final = str.maketrans(
        {
            # 0
            "O": "0",
            "o": "0",
            "Ο": "0",
            "О": "0",
            "〇": "0",
            # 1
            "I": "1",
            "l": "1",
            "|": "1",
            "!": "1",
            # 2
            "Z": "2",
            "z": "2",
            # 3
            "E": "3",
            "e": "3",
            # 4
            "A": "4",
            "a": "4",
            # 5
            "S": "5",
            "s": "5",
            "$": "5",
            # 6
            "G": "6",
            # 7
            "T": "7",
            "t": "7",
            # 8
            "B": "8",
            "b": "8",
            # 9
            "g": "9",
            "q": "9",
        }
    )

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
        if not self.lines:
            return result

        lines = self.lines[:]

        result["quality"], result["name"], lines = self._parse_item_quality_name(lines)
        result["base"], result["slot"], result["tier"], lines = self._parse_item_base_slot_tier(lines)
        if result["quality"] == Q.BASE.value:
            result["name"] = result["base"]

        result["requirements"], result["stats"], result["affixes"], lines = self._parse_requirements_stats_affixes(
            lines
        )

        return result

    def _normalize_skill(self, line: str) -> str:
        skill, _, _ = process.extractOne(
            line, self.R.get("skills", {}), scorer=fuzz.token_set_ratio, processor=str.lower, score_cutoff=90
        ) or (None, 0, None)
        if skill:
            align = fuzz.partial_ratio_alignment(line, skill, processor=str.lower)
            start, end = align.src_start, align.src_end
            line = line[:start] + "[Skill]" + line[end:]

        return line, skill

    def _normalize_numbers(self, line: str) -> str:
        numbers = re.findall(self._num_like, line)
        line = re.sub(self._num_like, "#", line)
        return line, [self._text_to_int(n) for n in numbers]

    def _text_to_int(self, s: str) -> int:
        """
        Convert a string containing OCR/leet-like confusables into an integer.
        - Transliterates a conservative set of visually confusable characters into ASCII digits.
        - Keeps any Unicode decimal digits as-is (Python int() accepts them).
        - Ignores non-digits after transliteration.
        """
        normalized = s.translate(self._digit_translation)
        digits = [ch for ch in normalized if ch.isdigit()]
        if not digits:
            return 0
        return int("".join(digits))

    def _join_params(self, line, numbers, skill):
        params = []
        num_idx = 0
        for match in re.finditer(r"#|\[Skill\]", line):
            token = match.group(0)
            if token == "#" and num_idx < len(numbers):
                params.append(numbers[num_idx])
                num_idx += 1
            elif token == "[Skill]" and skill:
                params.append(skill)
        return params

    def _match_class(self, query):
        class_, _, _ = process.extractOne(
            query, self.R.get("classes", {}), scorer=fuzz.partial_token_set_ratio, score_cutoff=100
        ) or (None, 0, None)
        if class_:
            align = fuzz.partial_ratio_alignment(query, class_, processor=str.lower)
            return query[align.src_start : align.src_end]

    def _parse_item_quality_name(self, lines):
        name_line = lines[0].strip()

        match, _, _ = process.extractOne(
            name_line, self.R.get("runewords", {}).keys(), scorer=fuzz.ratio, processor=str.lower, score_cutoff=85
        ) or (None, 0, None)
        if match:
            return Q.RUNEWORD.value, match, lines[1:]

        for scorer in self._scorers:
            match, _, _ = process.extractOne(
                name_line, self.R.get("uniques", {}).keys(), scorer=scorer, processor=str.lower, score_cutoff=85
            ) or (None, 0, None)
            if match:
                return Q.UNIQUE.value, match, lines[1:]

        for scorer in self._scorers:
            match, _, _ = process.extractOne(
                name_line, self.R.get("set", {}).keys(), scorer=scorer, processor=str.lower, score_cutoff=85
            ) or (None, 0, None)
            if match:
                return Q.SET.value, match, lines[1:]

        rares = self.R.get("rares", {})
        prefix, _, _ = (
            process.extractOne(
                name_line, rares["prefixes"], scorer=fuzz.partial_ratio, processor=str.lower, score_cutoff=90
            )
            or self._none_match
        )
        suffix, _, _ = (
            process.extractOne(
                name_line, rares["suffixes"], scorer=fuzz.partial_ratio, processor=str.lower, score_cutoff=90
            )
            or self._none_match
        )
        name = f"{prefix} {suffix}".strip()
        if name.lower() == name_line.lower():
            return Q.RARE.value, name, lines[1:]

        magic = self.R.get("magic", {})
        prefix, _, _ = (
            process.extractOne(
                name_line, magic["prefixes"], scorer=fuzz.token_set_ratio, processor=str.lower, score_cutoff=85
            )
            or self._none_match
        )
        suffix, _, _ = (
            process.extractOne(
                name_line, magic["suffixes"], scorer=fuzz.token_set_ratio, processor=str.lower, score_cutoff=85
            )
            or self._none_match
        )
        name = ((f"{prefix} " if prefix else "") + (suffix or "")).strip()
        if prefix or suffix:
            return Q.MAGIC.value, name, lines

        return Q.BASE.value, None, lines

    def _parse_item_base_slot_tier(self, lines):
        base_line = lines[0].strip()
        bases = self.R.get("bases", {})

        for scorer in self._scorers:
            matches = process.extract(base_line, bases.keys(), scorer=scorer, score_cutoff=85)
            if matches:
                longest_match = max(matches, key=lambda m: len(m[0]))
                return longest_match[0], bases[longest_match[0]]["slot"], bases[longest_match[0]]["tier"], lines[1:]

        return None, None, None, lines

    def _parse_requirements_stats_affixes(self, lines):
        requirements = {}
        stats = {}
        affixes = []
        remaining_lines = []

        for line in lines:
            normal_line, numbers = self._normalize_numbers(line)

            requirement, _, _ = process.extractOne(
                normal_line,
                self.R.get("requirements", {}).keys(),
                scorer=fuzz.ratio,
                processor=str.lower,
                score_cutoff=85,
            ) or (None, 0, None)
            if requirement:
                requirements[self.R.get("requirements", {})[requirement]] = (
                    numbers[0] if numbers else self._match_class(requirement)
                )
                continue

            stat, _, _ = process.extractOne(
                normal_line, self.R.get("stats", {}).keys(), scorer=fuzz.ratio, processor=str.lower, score_cutoff=85
            ) or (None, 0, None)
            if stat:
                stats[self.R.get("stats", {})[stat]] = numbers
                continue

            affix, _, _ = process.extractOne(
                normal_line, self.R.get("affixes", {}), scorer=fuzz.ratio, processor=str.lower, score_cutoff=85
            ) or (None, 0, None)
            if affix:
                affixes.append((affix, numbers))
                continue

            normal_line, skill = self._normalize_skill(normal_line)
            skill_affix, _, _ = process.extractOne(
                normal_line, self.R.get("affixes", {}), scorer=fuzz.ratio, processor=str.lower, score_cutoff=85
            ) or (None, 0, None)
            if skill_affix:
                affixes.append((skill_affix, self._join_params(normal_line, numbers, skill)))
                continue

            remaining_lines.append(line)

        return requirements, stats, affixes, remaining_lines
