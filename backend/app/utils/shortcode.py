"""
Game short code generation utility.

Generates memorable 2-3 word codes for game IDs (e.g., "blue-tiger-42").
"""

import random
from typing import Set

# Curated word lists for memorable codes
ADJECTIVES = [
    "happy", "clever", "brave", "bright", "swift",
    "calm", "bold", "wise", "quick", "proud",
    "sharp", "cool", "warm", "free", "kind",
    "fair", "sure", "true", "wild", "pure",
    "keen", "able", "aware", "agile", "alert",
    "smart", "witty", "jolly", "merry", "noble",
    "royal", "grand", "prime", "vital", "zesty",
    "peppy", "perky", "chipper", "bouncy", "lively",
]

NOUNS = [
    "tiger", "eagle", "dragon", "phoenix", "falcon",
    "wolf", "bear", "lion", "hawk", "panther",
    "fox", "owl", "raven", "cobra", "lynx",
    "puma", "jaguar", "cheetah", "leopard", "otter",
    "beaver", "badger", "wombat", "koala", "panda",
    "dolphin", "whale", "shark", "octopus", "mantis",
    "spider", "beetle", "hornet", "wasp", "cricket",
    "turtle", "tortoise", "gecko", "iguana", "newt",
]


def generate_short_code(existing_codes: Set[str] = None) -> str:
    """
    Generate a unique short code for a game.

    Format: adjective-noun-number (e.g., "brave-tiger-42")

    Args:
        existing_codes: Set of codes already in use (for collision avoidance)

    Returns:
        A unique short code string
    """
    if existing_codes is None:
        existing_codes = set()

    max_attempts = 100
    for _ in range(max_attempts):
        adjective = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)
        number = random.randint(10, 99)

        code = f"{adjective}-{noun}-{number}"

        if code not in existing_codes:
            return code

    # Fallback if we somehow can't generate unique code
    # This is extremely unlikely with 40 * 40 * 90 = 144,000 combinations
    import uuid
    return f"game-{uuid.uuid4().hex[:8]}"


def validate_short_code(code: str) -> bool:
    """
    Validate that a short code has the correct format.

    Args:
        code: The short code to validate

    Returns:
        True if valid, False otherwise
    """
    if not code:
        return False

    parts = code.split("-")

    # Should have 3 parts: adjective-noun-number
    if len(parts) != 3:
        return False

    adjective, noun, number_str = parts

    # Check if parts are valid
    if adjective not in ADJECTIVES:
        return False

    if noun not in NOUNS:
        return False

    # Check if number is valid (10-99)
    try:
        number = int(number_str)
        if number < 10 or number > 99:
            return False
    except ValueError:
        return False

    return True


def normalize_short_code(code: str) -> str:
    """
    Normalize a short code to lowercase with hyphens.

    Args:
        code: The code to normalize (can have spaces, mixed case, etc.)

    Returns:
        Normalized code string
    """
    # Replace spaces with hyphens, convert to lowercase
    normalized = code.lower().strip()
    normalized = normalized.replace(" ", "-").replace("_", "-")

    # Remove multiple consecutive hyphens
    while "--" in normalized:
        normalized = normalized.replace("--", "-")

    return normalized
