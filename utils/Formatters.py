import re

def parse_sub_count(value) -> int:
    """
    Accepts:
    - int / None
    - '144 subscribers'
    - '66K subscribers'
    - '1.2M subscribers'
    Returns int
    """
    if value is None:
        return 0

    if isinstance(value, int):
        return value

    if not isinstance(value, str):
        return 0

    text = value.lower().replace("subscribers", "").strip()

    match = re.match(r"([\d\.]+)\s*([km]?)", text)
    if not match:
        return 0

    number, suffix = match.groups()
    number = float(number)

    if suffix == "k":
        return int(number * 1_000)
    if suffix == "m":
        return int(number * 1_000_000)

    return int(number)

def format_sub_count(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)
