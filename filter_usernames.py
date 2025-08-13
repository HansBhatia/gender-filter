import re
import sys
from pathlib import Path
from rapidfuzz import fuzz, process
import gender_guesser.detector as gender

# --------- CONFIG ---------
INPUT_FILE = "usernames.txt"
OUT_MALE = "filtered_male.txt"
OUT_BIZ = "rejected_business.txt"
OUT_REST = "rejected_female_or_ambiguous.txt"
OUT_STATS = "stats.txt"

# Keywords you want to exclude (lowercase). Add/remove freely.
BUSINESS_KEYWORDS = {
    # core from your ask
    "hotel", "agency", "consult", "consulting", "yacht", "yatching", "yachter", "club", "clubs",
    "restaurant", "ristorante", "trattoria", "bistro", "bar", "grill", "cafe", "cafeteria",
    # broader business terms (cheap to include, good recall)
    "corp", "inc", "ltd", "llc", "co", "company", "enterprises", "enterprise",
    "group", "holdings", "partners", "capital", "ventures", "studio", "media",
    "marketing", "logistics", "shipping", "freight", "travel", "tour", "tours",
    "rentals", "rental", "resort", "spa", "salon", "nails", "boutique", "shop", "store",
    "management", "agencia", "agence", "consultoria", "consultoria", "agencja",
    "hostel", "motel", "guesthouse", "inn", "lounge", "steakhouse", "canteen",
    "catering", "bakery", "pizzeria", "sushi", "kebab", "taverna", "pub", "brewery"
}

# Optional: brand lists etc. Leave empty or extend.
BUSINESS_BRANDS = {
    # add known chains if you want to be more aggressive:
    "marriott", "hilton", "hyatt", "accor", "ihg", "ritz", "sheraton", "fourseasons",
    "mcdonalds", "burgerking", "dominos", "kfc", "subway", "starbucks"
}

# If a username contains ANY of these substrings (case-insensitive), we’ll mark as business.
BIZ_SUBSTRINGS = BUSINESS_KEYWORDS | BUSINESS_BRANDS

# Optional fuzzy matching for “close” typos (e.g., yact -> yacht). Keep small for speed.
# Map common misspellings to their intended keyword.
FUZZY_MAP = {
    "yact": "yacht",
    "restraunt": "restaurant",
    "resto": "restaurant",
    "agance": "agency",
}
FUZZY_THRESHOLD = 90  # 0-100; higher = stricter

# --------- HELPERS ---------
alpha_re = re.compile(r"[A-Za-z]+")
split_re = re.compile(r"[._\-|/\\\s]+")

det = gender.Detector(case_sensitive=False)

def is_business(username_lc: str) -> bool:
    # fast substring check
    for kw in BIZ_SUBSTRINGS:
        if kw in username_lc:
            return True
    # light fuzzy: token-level check only if needed
    # Split username into tokens and fuzzy match common misspellings
    tokens = split_re.split(username_lc)
    for t in tokens:
        if not t:
            continue
        # only check short tokens to avoid slowdowns
        if len(t) <= 12:
            best = process.extractOne(t, FUZZY_MAP.keys(), scorer=fuzz.ratio)
            if best and best[1] >= FUZZY_THRESHOLD:
                return True
    return False

def first_name_like_token(username: str) -> str | None:
    # Pick the first alphabetic token that looks like a name (letters only)
    # e.g., "john_smith23" -> "john"; "xx_mike-90" -> "mike"
    # If nothing obvious, return None.
    # Try splits on separators first
    parts = split_re.split(username)
    for p in parts:
        m = alpha_re.fullmatch(p)
        if m:
            return m.group(0)
    # Fallback: find any alpha run
    m = alpha_re.search(username)
    return m.group(0).lower() if m else None

def is_male_name(name_token: str) -> bool:
    # gender-guesser returns: 'male', 'mostly_male', 'female', 'mostly_female', 'andy', 'unknown'
    g = det.get_gender(name_token)
    return g in ("male", "mostly_male")

def is_female_or_ambiguous(name_token: str) -> bool:
    g = det.get_gender(name_token)
    return g in ("female", "mostly_female", "andy", "unknown")

# --------- MAIN ---------
def main():
    src = Path(INPUT_FILE)
    if not src.exists():
        print(f"Input file not found: {src.resolve()}", file=sys.stderr)
        sys.exit(1)

    out_male = open(OUT_MALE, "w", encoding="utf-8")
    out_biz = open(OUT_BIZ, "w", encoding="utf-8")
    out_rest = open(OUT_REST, "w", encoding="utf-8")

    n_total = n_biz = n_male = n_rest = 0

    with open(src, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            username = line.strip()
            if not username:
                continue
            n_total += 1
            u_lc = username.lower()

            # 1) Business filter
            if is_business(u_lc):
                out_biz.write(username + "\n")
                n_biz += 1
                continue

            # 2) Gender filter
            token = first_name_like_token(u_lc)
            if token and is_male_name(token):
                out_male.write(username + "\n")
                n_male += 1
            else:
                out_rest.write(username + "\n")
                n_rest += 1

    out_male.close()
    out_biz.close()
    out_rest.close()

    with open(OUT_STATS, "w", encoding="utf-8") as s:
        s.write(f"Total read: {n_total}\n")
        s.write(f"Business rejected: {n_biz}\n")
        s.write(f"Kept male: {n_male}\n")
        s.write(f"Female/ambiguous/unknown: {n_rest}\n")

    print("Done.")
    print(f"Kept male -> {OUT_MALE}")
    print(f"Business -> {OUT_BIZ}")
    print(f"Female/ambiguous/unknown -> {OUT_REST}")
    print(f"Stats -> {OUT_STATS}")

if __name__ == "__main__":
    main()