"""
Layer 3 — Challenge-Response + EMA - Aditya
Handles dynamic challenges, HMAC-signed token verification with 90s TTL,
single-use enforcement, and adaptive EMA voiceprint updates.
"""

import os
import secrets
import hmac
import hashlib
import random
from datetime import datetime, timedelta
from typing import Optional

# Secret key for HMAC token signing (can be loaded from environment)
SECRET_KEY = os.getenv("L3_HMAC_SECRET", "aaa_engine_l3_adaptive_secret_key_2026").encode()

# =============================================================================
# EXTENSIVE WORD POOLS FOR UNIQUE PHRASE GENERATION
# Each phrase is dynamically generated - virtually unlimited combinations
# =============================================================================

# Numbers (spoken form)
NUMBERS = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty",
    "sixty", "seventy", "eighty", "ninety", "hundred"
]

# Colors - extensive list
COLORS = [
    "red", "blue", "green", "yellow", "orange", "purple", "pink", "brown",
    "black", "white", "gray", "silver", "gold", "bronze", "copper",
    "crimson", "scarlet", "maroon", "ruby", "coral", "salmon", "peach",
    "amber", "golden", "honey", "mustard", "lemon", "lime", "olive",
    "emerald", "jade", "mint", "teal", "turquoise", "cyan", "aqua",
    "navy", "cobalt", "indigo", "violet", "lavender", "plum", "magenta",
    "rose", "burgundy", "ivory", "cream", "beige", "tan", "khaki"
]

# Animals - easy to pronounce
ANIMALS = [
    "falcon", "eagle", "hawk", "owl", "raven", "sparrow", "robin", "dove",
    "phoenix", "dragon", "griffin", "panther", "tiger", "lion", "leopard",
    "wolf", "fox", "bear", "deer", "elk", "moose", "buffalo", "bison",
    "horse", "zebra", "dolphin", "whale", "shark", "salmon", "trout",
    "cobra", "python", "viper", "falcon", "condor", "pelican", "crane",
    "heron", "swan", "goose", "duck", "penguin", "puffin", "parrot",
    "jaguar", "cheetah", "cougar", "lynx", "bobcat", "otter", "beaver",
    "rabbit", "squirrel", "chipmunk", "hedgehog", "badger", "raccoon"
]

# Objects - tangible things
OBJECTS = [
    "shield", "sword", "arrow", "spear", "hammer", "anchor", "compass",
    "crystal", "diamond", "emerald", "ruby", "sapphire", "pearl", "opal",
    "mountain", "river", "ocean", "forest", "desert", "island", "valley",
    "castle", "tower", "bridge", "gateway", "fortress", "temple", "palace",
    "sunrise", "sunset", "moonlight", "starlight", "thunder", "lightning",
    "beacon", "lantern", "torch", "candle", "mirror", "window", "doorway",
    "garden", "meadow", "orchard", "vineyard", "harbor", "lighthouse",
    "canyon", "glacier", "volcano", "waterfall", "rainbow", "horizon"
]

# Abstract concepts - meaningful words
CONCEPTS = [
    "nexus", "matrix", "cipher", "prism", "echo", "pulse", "spark",
    "spirit", "shadow", "light", "flame", "frost", "storm", "breeze",
    "harmony", "balance", "unity", "wisdom", "courage", "honor", "valor",
    "justice", "mercy", "grace", "truth", "peace", "freedom", "victory",
    "journey", "quest", "mission", "voyage", "venture", "passage", "path",
    "legacy", "heritage", "destiny", "fortune", "wonder", "marvel", "dream",
    "vision", "insight", "clarity", "focus", "purpose", "resolve", "strength"
]

# Adjectives - descriptive words
ADJECTIVES = [
    "swift", "brave", "bold", "calm", "wise", "keen", "bright", "clear",
    "strong", "gentle", "noble", "loyal", "true", "pure", "grand", "great",
    "ancient", "modern", "classic", "timeless", "endless", "boundless",
    "silent", "peaceful", "tranquil", "serene", "graceful", "elegant",
    "mighty", "powerful", "fearless", "steadfast", "resolute", "determined",
    "radiant", "brilliant", "luminous", "vibrant", "vivid", "dynamic",
    "majestic", "regal", "royal", "supreme", "prime", "premier", "stellar",
    "cosmic", "eternal", "infinite", "pristine", "crystal", "diamond"
]

# Verbs (action words in imperative/present form)
VERBS = [
    "soar", "glide", "leap", "dash", "sprint", "march", "stride", "venture",
    "guard", "shield", "protect", "defend", "secure", "watch", "observe",
    "seek", "find", "discover", "explore", "journey", "travel", "roam",
    "shine", "glow", "spark", "blaze", "flare", "flash", "gleam", "beam",
    "rise", "climb", "ascend", "lift", "surge", "flow", "drift", "float",
    "unite", "join", "connect", "link", "bind", "forge", "craft", "build",
    "lead", "guide", "direct", "steer", "navigate", "chart", "pioneer"
]

# Locations/Places
PLACES = [
    "north", "south", "east", "west", "central", "coastal", "highland",
    "summit", "peak", "ridge", "cliff", "shore", "bay", "cove", "inlet",
    "grove", "glade", "clearing", "hollow", "dell", "glen", "vale",
    "plaza", "square", "court", "avenue", "boulevard", "terrace", "arcade",
    "station", "terminal", "junction", "crossing", "gateway", "portal"
]

# Time references
TIME_WORDS = [
    "dawn", "dusk", "twilight", "midnight", "noon", "morning", "evening",
    "spring", "summer", "autumn", "winter", "solstice", "equinox",
    "century", "decade", "moment", "instant", "epoch", "era", "age"
]

# =============================================================================
# PHRASE TEMPLATES - Multiple structures for variety
# =============================================================================

def _generate_dynamic_phrase() -> str:
    """
    Generate a unique, speakable challenge phrase.

    Uses multiple templates and extensive word pools to create
    virtually unlimited unique combinations.

    Entropy calculation:
    - Template 1: 30 × 50 × 55 × 30 = 2,475,000 combinations
    - Template 2: 50 × 50 × 55 = 137,500 combinations
    - Template 3: 50 × 30 × 55 × 50 = 4,125,000 combinations
    - Template 4: 30 × 55 × 50 × 35 = 2,887,500 combinations
    - Template 5: 50 × 55 × 35 × 30 = 2,887,500 combinations
    - Template 6: 50 × 55 × 45 × 50 = 6,187,500 combinations
    - Template 7: 30 × 50 × 55 × 45 = 3,712,500 combinations
    - Plus sentence templates with even more combinations

    Total: Tens of millions of unique phrases possible
    """
    template = random.randint(1, 12)

    if template == 1:
        # Pattern: "Say: NUMBER COLOR ANIMAL NUMBER"
        return f"Say: {random.choice(NUMBERS)} {random.choice(COLORS)} {random.choice(ANIMALS)} {random.choice(NUMBERS)}"

    elif template == 2:
        # Pattern: "Say: COLOR ADJECTIVE OBJECT"
        return f"Say: {random.choice(COLORS)} {random.choice(ADJECTIVES)} {random.choice(OBJECTS)}"

    elif template == 3:
        # Pattern: "Say: ADJECTIVE COLOR ANIMAL VERB"
        return f"Say: {random.choice(ADJECTIVES)} {random.choice(COLORS)} {random.choice(ANIMALS)} {random.choice(VERBS)}"

    elif template == 4:
        # Pattern: "Say: NUMBER CONCEPT COLOR PLACE"
        return f"Say: {random.choice(NUMBERS)} {random.choice(CONCEPTS)} {random.choice(COLORS)} {random.choice(PLACES)}"

    elif template == 5:
        # Pattern: "Say: COLOR ANIMAL PLACE NUMBER"
        return f"Say: {random.choice(COLORS)} {random.choice(ANIMALS)} {random.choice(PLACES)} {random.choice(NUMBERS)}"

    elif template == 6:
        # Pattern: "Say: ADJECTIVE CONCEPT VERB OBJECT"
        return f"Say: {random.choice(ADJECTIVES)} {random.choice(CONCEPTS)} {random.choice(VERBS)} {random.choice(OBJECTS)}"

    elif template == 7:
        # Pattern: "Say: NUMBER ADJECTIVE ANIMAL TIME"
        return f"Say: {random.choice(NUMBERS)} {random.choice(ADJECTIVES)} {random.choice(ANIMALS)} {random.choice(TIME_WORDS)}"

    elif template == 8:
        # Sentence: "The ADJECTIVE COLOR ANIMAL VERB"
        return f"The {random.choice(ADJECTIVES)} {random.choice(COLORS)} {random.choice(ANIMALS)} {random.choice(VERBS)}"

    elif template == 9:
        # Sentence: "VERB the ADJECTIVE OBJECT at TIME"
        verb = random.choice(VERBS).capitalize()
        return f"{verb} the {random.choice(ADJECTIVES)} {random.choice(OBJECTS)} at {random.choice(TIME_WORDS)}"

    elif template == 10:
        # Sentence: "A COLOR ANIMAL guards the CONCEPT"
        return f"A {random.choice(COLORS)} {random.choice(ANIMALS)} guards the {random.choice(CONCEPTS)}"

    elif template == 11:
        # Sentence: "The CONCEPT of NUMBER ADJECTIVE OBJECTS"
        return f"The {random.choice(CONCEPTS)} of {random.choice(NUMBERS)} {random.choice(ADJECTIVES)} {random.choice(OBJECTS)}"

    else:  # template == 12
        # Sentence: "From PLACE to PLACE the ANIMAL travels"
        return f"From {random.choice(PLACES)} to {random.choice(PLACES)} the {random.choice(ANIMALS)} travels"

# In-memory token store: maps token_str -> token_metadata
_token_store: dict[str, dict] = {}


def generate_challenge(user_id: str) -> dict:
    """
    Generate a dynamic challenge phrase and single-use HMAC-SHA256 signed token with 90s TTL.

    Args:
        user_id: UUID of the user requesting authentication

    Returns:
        {"phrase": str, "token": str, "expires_at": datetime}
    """
    phrase = _generate_dynamic_phrase()
    
    # Expiration: strictly 90 seconds (per shared contract section 6 & layer3 spec)
    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=90)
    expires_timestamp = str(int(expires_at.timestamp()))
    
    # Create raw payload and sign with HMAC-SHA256
    raw_nonce = secrets.token_hex(16)
    raw_payload = f"{user_id}:{expires_timestamp}:{phrase}:{raw_nonce}"
    signature = hmac.new(SECRET_KEY, raw_payload.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # URL-safe HMAC token
    token = f"{raw_nonce}.{expires_timestamp}.{signature}"

    # Store token for single-use & tracking
    _token_store[token] = {
        "user_id": user_id,
        "phrase": phrase,
        "expires_at": expires_at,
        "payload": raw_payload,
        "signature": signature,
        "used": False
    }

    return {
        "phrase": phrase,
        "token": token,
        "expires_at": expires_at
    }


def verify_token(token: str) -> bool:
    """
    Verify token is valid (exists, HMAC valid, not expired, not used).
    Enforces single-use by marking token as used immediately.

    Args:
        token: Challenge token to verify

    Returns:
        True if token is valid and now consumed, False otherwise
    """
    if not token or token not in _token_store:
        return False

    token_data = _token_store[token]

    # 1. Single-use check
    if token_data.get("used", False):
        return False

    # 2. TTL Expiration check (90s limit)
    now = datetime.utcnow()
    if now > token_data["expires_at"]:
        # Remove expired token
        del _token_store[token]
        return False

    # 3. HMAC Signature integrity check
    raw_payload = token_data.get("payload", "")
    expected_sig = hmac.new(SECRET_KEY, raw_payload.encode('utf-8'), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(token_data.get("signature", ""), expected_sig):
        return False

    # Consume token (single-use enforcement)
    token_data["used"] = True

    return True


def get_token_user_id(token: str) -> Optional[str]:
    """Get the user_id associated with a token."""
    if token in _token_store:
        return _token_store[token]["user_id"]
    return None


def get_token_phrase(token: str) -> Optional[str]:
    """Get the challenge phrase associated with a token."""
    if token in _token_store:
        return _token_store[token]["phrase"]
    return None


def update_voiceprint(
    old_embedding: list[float],
    new_embedding: list[float],
    alpha: float = 0.2
) -> list[float]:
    """
    Exponential Moving Average update of voiceprint.
    Formula: New = (1 - alpha) * Old + alpha * Current
    With alpha = 0.2: New = 0.8 * Old + 0.2 * Current
    (weights Current embedding by 0.2, Old by 0.8)

    Args:
        old_embedding: Current stored embedding (192-dim)
        new_embedding: New embedding from successful authentication (192-dim)
        alpha: Weight for current embedding (default 0.2)

    Returns:
        Updated embedding vector (same dimension)
    """
    if len(old_embedding) != len(new_embedding):
        raise ValueError(
            f"Embedding dimension mismatch: {len(old_embedding)} vs {len(new_embedding)}"
        )

    # Calculate elementwise: 0.8 * old + 0.2 * current
    updated = [
        (1.0 - alpha) * old_val + alpha * new_val
        for old_val, new_val in zip(old_embedding, new_embedding)
    ]

    return updated

