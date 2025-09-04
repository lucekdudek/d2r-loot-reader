import json
import re
from typing import Any, Dict, List, Optional, Tuple

from rapidfuzz import fuzz, process

from d2rlootreader.cfg import REPOSITORY_DIR


def load_repository_data() -> Dict[str, Any]:
    data = {}
    for fname in REPOSITORY_DIR.glob("*.json"):
        with open(fname, encoding="utf-8") as f:
            data[fname.stem] = json.load(f)
    return data


def _match_quality_and_name(lines: List[str], repo: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    candidates = [
        ("runewords", "Runeword"),
        ("setitems", "Set"),
        ("uniqueitems", "Unique"),
        ("rares", "Rare"),
        ("magic", "Magic"),
        ("weapons", "Base"),
        ("armor", "Base"),
    ]
    top_lines = lines[:2]
    for repo_key, quality in candidates:
        names = [item["name"] for item in repo.get(repo_key, []) if "name" in item]
        for line in top_lines:
            match, score, idx = process.extractOne(line, names, scorer=fuzz.ratio, score_cutoff=80) or (None, 0, None)
            if match:
                print(
                    f"[item_parser] Matched quality '{quality}' and name '{match}' using repo '{repo_key}' and line '{line}' (score={score})"
                )
                return quality, match
    # No fallback here; let main function handle magic/rare fallback
    print("[item_parser] Could not determine item quality or name after all matching attempts.")
    return None, None


def _parse_requirements(lines: List[str]) -> Tuple[Dict[str, Any], List[int]]:
    req = {}
    used = []
    for idx, line in enumerate(lines):
        m = re.search(r"^Required Strength: (\d+)$", line, re.I)
        if m:
            req["strength"] = int(m.group(1))
            used.append(idx)
        m = re.search(r"^Required Dexterity: (\d+)$", line, re.I)
        if m:
            req["dexterity"] = int(m.group(1))
            used.append(idx)
        m = re.search(r"^Required Level: (\d+)$", line, re.I)
        if m:
            req["level"] = int(m.group(1))
            used.append(idx)
        else:
            # Try to catch OCR errors like "Required Level: S"
            m2 = re.search(r"^Required Level: (\w+)$", line, re.I)
            if m2:
                val = m2.group(1)
                ocr_map = {"S": "3", "O": "0", "I": "1", "B": "8"}
                corrected = "".join(ocr_map.get(c, c) for c in val)
                if corrected.isdigit():
                    req["level"] = int(corrected)
                    print(f"[item_parser] Corrected OCR Required Level '{val}' to {corrected}")
                else:
                    req["level"] = val
                    print(f"[item_parser] Warning: Unrecognized level requirement '{val}' in line: '{line}'")
                used.append(idx)
        m = re.fullmatch(r"\((\w+) Only\)", line.strip())
        if m:
            req["class"] = m.group(1)
            used.append(idx)
    return req, used


def _parse_stats(lines: List[str]) -> Tuple[Dict[str, Any], List[int]]:
    stats = {}
    used = []
    for idx, line in enumerate(lines):
        m = re.search(r"^Defense: (\d+)$", line, re.I)
        if m:
            stats["defense"] = int(m.group(1))
            used.append(idx)
        m = re.search(r"^One[- ]Hand Damage: (\d+)[^\d]+(\d+)$", line, re.I)
        if m:
            stats["one_hand_damage"] = [int(m.group(1)), int(m.group(2))]
            used.append(idx)
        m = re.search(r"^Two[- ]Hand Damage: (\d+)[^\d]+(\d+)$", line, re.I)
        if m:
            stats["two_hand_damage"] = [int(m.group(1)), int(m.group(2))]
            used.append(idx)
    return stats, used


def _template_to_regex(template: str) -> str:
    pattern = re.escape(template)
    pattern = pattern.replace(r"\#", r"(-?\d+)")
    pattern = re.sub(r"\\\[.*?\\\]", r"(.+?)", pattern)
    pattern = pattern.replace(r"\ ", r"\s+")
    return "^" + pattern + "$"


def _parse_affixes(lines, repo, skip_idxs):
    affix_dict = {}
    affix_templates = repo.get("affixes", [])
    skills = repo.get("skills", [])
    classes = repo.get("classes", [])
    template_regexes = {tpl: re.compile(_template_to_regex(tpl), re.I) for tpl in affix_templates}
    for idx, line in enumerate(lines):
        if idx in skip_idxs:
            continue
        matched = False
        m = re.match(r"\+(\d+)\s+to\s+([A-Za-z' ]+)\s+\((\w+) Only\)", line)
        if m:
            num = int(m.group(1))
            skill = m.group(2).strip()
            cls = m.group(3).strip()
            skill_match, _, _ = process.extractOne(skill, skills, scorer=fuzz.ratio, score_cutoff=70) or (None, 0, None)
            class_match, _, _ = process.extractOne(cls, classes, scorer=fuzz.ratio, score_cutoff=70) or (None, 0, None)
            if skill_match and class_match:
                affix_dict["+# to [Skill] ([Class] only)"] = [num, skill_match, class_match]
                print(f"[item_parser] Matched skill/class affix: +{num} to {skill_match} ({class_match} Only)")
                continue
        for tpl, regex in template_regexes.items():
            m = regex.match(line)
            if m:
                values = []
                for group, part in zip(m.groups(), re.findall(r"#|\[.*?\]", tpl)):
                    if part == "#":
                        values.append(int(group))
                    else:
                        values.append(group.strip())
                affix_dict[tpl] = values
                print(f"[item_parser] Matched affix '{tpl}' with values {values} from line '{line}'")
                matched = True
                break
        if not matched:
            print(f"[item_parser] Affix not matched for line: '{line}'")
    return affix_dict


def _collect_bases_and_slots(repo: Dict[str, Any]) -> Tuple[List[str], Dict[str, Tuple[str, str]]]:
    all_base_names = []
    base_to_slot_and_tier = {}
    for slot_type, bases in repo.get("armor", {}).items():
        for base, tier in bases.items():
            all_base_names.append(base)
            base_to_slot_and_tier[base] = (slot_type, tier)
    for slot_type, bases in repo.get("weapons", {}).items():
        for base, tier in bases.items():
            all_base_names.append(base)
            base_to_slot_and_tier[base] = (slot_type, tier)
    return all_base_names, base_to_slot_and_tier


def _extract_affix_base(
    line: str, repo: Dict[str, Any], all_base_names: List[str]
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    # Try rare first
    rare = repo.get("rares", {})
    rare_prefixes = rare.get("prefixes", [])
    rare_suffixes = rare.get("suffixes", [])
    magic = repo.get("magic", {})
    magic_prefixes = magic.get("prefixes", [])
    magic_suffixes = magic.get("suffixes", [])

    # Try rare prefixes/suffixes
    rare_prefix, rare_prefix_score, _ = process.extractOne(
        line, rare_prefixes, scorer=fuzz.partial_ratio, score_cutoff=80
    ) or (None, 0, None)
    rare_suffix, rare_suffix_score, _ = process.extractOne(
        line, rare_suffixes, scorer=fuzz.partial_ratio, score_cutoff=80
    ) or (None, 0, None)
    base_candidate = line
    if rare_prefix and line.startswith(rare_prefix):
        base_candidate = base_candidate[len(rare_prefix) :].strip()
    if rare_suffix and base_candidate.endswith(rare_suffix):
        base_candidate = base_candidate[: -len(rare_suffix)].strip()
    if base_candidate.endswith("of"):
        base_candidate = base_candidate[:-2].strip()
    base_match, base_score, _ = process.extractOne(
        base_candidate, all_base_names, scorer=fuzz.ratio, score_cutoff=70
    ) or (None, 0, None)
    if rare_prefix or rare_suffix:
        if base_match:
            print(
                f"[item_parser] Rare fallback: Matched prefix '{rare_prefix}', base '{base_match}', suffix '{rare_suffix}' from '{line}'"
            )
            return "Rare", base_match, rare_prefix, rare_suffix

    # Try magic prefixes/suffixes
    magic_prefix, magic_prefix_score, _ = process.extractOne(
        line, magic_prefixes, scorer=fuzz.partial_ratio, score_cutoff=80
    ) or (None, 0, None)
    magic_suffix, magic_suffix_score, _ = process.extractOne(
        line, magic_suffixes, scorer=fuzz.partial_ratio, score_cutoff=80
    ) or (None, 0, None)
    base_candidate = line
    if magic_prefix and line.startswith(magic_prefix):
        base_candidate = base_candidate[len(magic_prefix) :].strip()
    if magic_suffix and base_candidate.endswith(magic_suffix):
        base_candidate = base_candidate[: -len(magic_suffix)].strip()
    if base_candidate.endswith("of"):
        base_candidate = base_candidate[:-2].strip()
    base_match, base_score, _ = process.extractOne(
        base_candidate, all_base_names, scorer=fuzz.ratio, score_cutoff=70
    ) or (None, 0, None)
    if magic_prefix or magic_suffix:
        if base_match:
            print(
                f"[item_parser] Magic fallback: Matched prefix '{magic_prefix}', base '{base_match}', suffix '{magic_suffix}' from '{line}'"
            )
            return "Magic", base_match, magic_prefix, magic_suffix

    print(f"[item_parser] Fallback: Could not extract base from '{line}' (rare/magic affix logic)")
    return None, None, None, None


def _extract_magic_base_prefix_suffix(
    line: str, repo: Dict[str, Any], all_base_names: List[str]
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    # Try to match prefix and suffix from magic.json
    magic = repo.get("magic", {})
    prefixes = magic.get("prefixes", [])
    suffixes = magic.get("suffixes", [])
    # Fuzzy match prefix
    prefix_match, prefix_score, _ = process.extractOne(line, prefixes, scorer=fuzz.partial_ratio, score_cutoff=80) or (
        None,
        0,
        None,
    )
    # Fuzzy match suffix
    suffix_match, suffix_score, _ = process.extractOne(line, suffixes, scorer=fuzz.partial_ratio, score_cutoff=80) or (
        None,
        0,
        None,
    )
    base_candidate = line
    if prefix_match and line.startswith(prefix_match):
        base_candidate = base_candidate[len(prefix_match) :].strip()
    if suffix_match and base_candidate.endswith(suffix_match):
        base_candidate = base_candidate[: -len(suffix_match)].strip()
    # Remove "of" if present before suffix
    if base_candidate.endswith("of"):
        base_candidate = base_candidate[:-2].strip()
    # Fuzzy match base
    base_match, base_score, _ = process.extractOne(
        base_candidate, all_base_names, scorer=fuzz.ratio, score_cutoff=70
    ) or (None, 0, None)
    if base_match:
        print(
            f"[item_parser] Magic fallback: Matched prefix '{prefix_match}', base '{base_match}', suffix '{suffix_match}' from '{line}'"
        )
        return base_match, prefix_match, suffix_match
    print(
        f"[item_parser] Magic fallback: Could not extract base from '{line}' (prefix: {prefix_match}, suffix: {suffix_match}, candidate: '{base_candidate}')"
    )
    return None, prefix_match, suffix_match


def _match_base_slot_tier(
    lines: List[str], repo: Dict[str, Any]
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[int]]:
    all_base_names, base_to_slot_and_tier = _collect_bases_and_slots(repo)
    for idx, line in enumerate(lines):
        match, score, _ = process.extractOne(line, all_base_names, scorer=fuzz.ratio, score_cutoff=80) or (
            None,
            0,
            None,
        )
        if match:
            slot, tier = base_to_slot_and_tier[match]
            print(
                f"[item_parser] Matched base '{match}', slot '{slot}', tier '{tier}' from line '{line}' (score={score})"
            )
            return match, slot, tier, idx
    print("[item_parser] Could not determine base item, slot, or tier after all matching attempts.")
    return None, None, None, None


def _detect_affix_quality(line: str, repo: Dict[str, Any]) -> Optional[str]:
    rare = repo.get("rares", {})
    magic = repo.get("magic", {})
    rare_prefixes = rare.get("prefixes", [])
    rare_suffixes = rare.get("suffixes", [])
    magic_prefixes = magic.get("prefixes", [])
    magic_suffixes = magic.get("suffixes", [])

    # Check rare prefixes/suffixes
    rare_prefix, rare_prefix_score, _ = process.extractOne(
        line, rare_prefixes, scorer=fuzz.partial_ratio, score_cutoff=90
    ) or (None, 0, None)
    rare_suffix, rare_suffix_score, _ = process.extractOne(
        line, rare_suffixes, scorer=fuzz.partial_ratio, score_cutoff=90
    ) or (None, 0, None)
    if (rare_prefix and line.startswith(rare_prefix)) or (rare_suffix and line.endswith(rare_suffix)):
        return "Rare"

    # Check magic prefixes/suffixes
    magic_prefix, magic_prefix_score, _ = process.extractOne(
        line, magic_prefixes, scorer=fuzz.partial_ratio, score_cutoff=90
    ) or (None, 0, None)
    magic_suffix, magic_suffix_score, _ = process.extractOne(
        line, magic_suffixes, scorer=fuzz.partial_ratio, score_cutoff=90
    ) or (None, 0, None)
    if (magic_prefix and line.startswith(magic_prefix)) or (magic_suffix and line.endswith(magic_suffix)):
        return "Magic"

    return None


def parse_item_lines_to_json(lines: List[str]) -> Dict[str, Any]:
    repo = load_repository_data()
    result = {
        "quality": None,
        "name": None,
        "base": None,
        "slot": None,
        "tier": None,
        "requirements": {},
        "stats": {},
        "affixes": {},
        "tooltip": lines,
    }
    result["quality"], result["name"] = _match_quality_and_name(lines, repo)
    base, slot, tier, base_idx = _match_base_slot_tier(lines, repo)
    result["base"], result["slot"], result["tier"] = base, slot, tier

    if result["quality"] is None and lines:
        detected_quality = _detect_affix_quality(lines[0], repo)
        if detected_quality:
            result["quality"] = detected_quality
            result["name"] = lines[0]
            print(f"[item_parser] Detected quality '{detected_quality}' from affix analysis of '{lines[0]}'")

    if (result["quality"] is None or result["base"] is None) and lines:
        if result["base"] is None:
            all_base_names, base_to_slot_and_tier = _collect_bases_and_slots(repo)
            quality, base, prefix, suffix = _extract_affix_base(lines[0], repo, all_base_names)
            if base:
                result["base"] = base
                slot, tier = base_to_slot_and_tier.get(base, (None, None))
                result["slot"] = slot
                result["tier"] = tier
                result["quality"] = quality
                result["name"] = lines[0]
                print(
                    f"[item_parser] Fallback: Set quality='{quality}', name='{lines[0]}', base='{base}', slot='{slot}', tier='{tier}', prefix='{prefix}', suffix='{suffix}'"
                )
            else:
                print("[item_parser] Fallback: Could not determine base/slot/tier from rare/magic name.")

    if result["base"] is None:
        print("[item_parser] Base item not found in lines or repository.")
    if result["slot"] is None:
        print("[item_parser] Slot not found for base item.")
    if result["tier"] is None:
        print("[item_parser] Tier not found for base item.")

    requirements, req_idxs = _parse_requirements(lines)
    result["requirements"] = requirements
    stats, stat_idxs = _parse_stats(lines)
    result["stats"] = stats
    skip_idxs = set(stat_idxs + req_idxs)
    if base_idx is not None:
        skip_idxs.add(base_idx)
    skip_idxs.add(0)  # name line
    result["affixes"] = _parse_affixes(lines, repo, skip_idxs)
    return result
