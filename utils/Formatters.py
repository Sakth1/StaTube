import re

from .Logger import logger

def parse_sub_count(value) -> int:
    """
    Accepts:
    - int / None
    - 'none'
    - '1 subscriber'
    - '144 subscribers'
    - '66.1K subscribers'
    - '1.2M subscribers'
    - '66.1 thousand'
    - '1.16 million'
    Returns int
    """
    if value is None:
        return 0

    if isinstance(value, int):
        return value

    if not isinstance(value, str):
        return 0

    text = (
        value.lower()
        .replace(",", "")
        .replace("subscribers", "")
        .replace("subscriber", "")
        .strip()
    )

    # Explicit "none"
    if text in ("none", ""):
        return 0

    # --- word-based units ---
    word_units = {
        "thousand": 1_000,
        "million": 1_000_000,
        "billion": 1_000_000_000,
    }

    for word, multiplier in word_units.items():
        if word in text:
            try:
                number = float(text.replace(word, "").strip())
                return int(number * multiplier)
            except ValueError:
                return 0

    # --- short suffix units (K / M / B) ---
    match = re.fullmatch(r"([\d]+(?:\.\d+)?)\s*([kmb]?)", text)
    if not match:
        return 0

    number_str, suffix = match.groups()

    try:
        number = float(number_str)
    except ValueError:
        logger.debug(f"Invalid number: {number_str}")
        return 0

    if suffix == "k":
        return int(number * 1_000)
    if suffix == "m":
        return int(number * 1_000_000)
    if suffix == "b":
        return int(number * 1_000_000_000)

    return int(number)

def format_sub_count(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)
