import re
from rapidfuzz import fuzz, process

# Business keywords to exclude (lowercase)
BUSINESS_KEYWORDS = {
    # Core business terms
    "hotel", "agency", "consult", "consulting", "yacht", "yachting", "yachter", "club", "clubs",
    "restaurant", "ristorante", "trattoria", "bistro", "bar", "grill", "cafe", "cafeteria",
    # Corporate terms
    "corp", "inc", "ltd", "llc", "co", "company", "enterprises", "enterprise",
    "group", "holdings", "partners", "capital", "ventures", "studio", "media",
    # Services
    "marketing", "logistics", "shipping", "freight", "travel", "tour", "tours",
    "rentals", "rental", "resort", "spa", "salon", "nails", "boutique", "shop", "store",
    "management", "agencia", "agence", "consultoria", "agencja",
    # Hospitality
    "hostel", "motel", "guesthouse", "inn", "lounge", "steakhouse", "canteen",
    "catering", "bakery", "pizzeria", "sushi", "kebab", "taverna", "pub", "brewery",
    # Additional
    "coach", "coaching", "trainer", "training", "services", "solutions"
}

# Known business brands
BUSINESS_BRANDS = {
    "marriott", "hilton", "hyatt", "accor", "ihg", "ritz", "sheraton", "fourseasons",
    "mcdonalds", "burgerking", "dominos", "kfc", "subway", "starbucks"
}

# Combined set
BIZ_SUBSTRINGS = BUSINESS_KEYWORDS | BUSINESS_BRANDS

# Common misspellings to catch
FUZZY_MAP = {
    "yact": "yacht",
    "restraunt": "restaurant",
    "resto": "restaurant",
    "agance": "agency",
}

FUZZY_THRESHOLD = 90  # 0-100; higher = stricter

# Regex patterns
split_re = re.compile(r"[._\-|/\\\s]+")


def is_business_account(username: str) -> tuple[bool, str]:
    """
    Check if username appears to be a business account.
    Returns (is_business, reason)
    """
    username_lc = username.lower()

    # Fast substring check
    for kw in BIZ_SUBSTRINGS:
        if kw in username_lc:
            return True, f"Business keyword: {kw}"

    # Fuzzy matching for common misspellings
    tokens = split_re.split(username_lc)
    for token in tokens:
        if not token or len(token) > 12:
            continue

        best = process.extractOne(token, FUZZY_MAP.keys(), scorer=fuzz.ratio)
        if best and best[1] >= FUZZY_THRESHOLD:
            return True, f"Fuzzy match: {token} -> {FUZZY_MAP[best[0]]}"

    return False, "Valid"