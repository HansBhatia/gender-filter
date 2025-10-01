import re

def is_gibberish(username: str) -> tuple[bool, str]:
    """
    Check if username is gibberish based on pastebin rules.
    Returns (is_gibberish, reason)
    """

    # Remove underscores and periods for analysis
    clean = re.sub(r'[_.\-]', '', username.lower())

    # Extract letters only for vowel/consonant analysis
    letters_only = re.sub(r'[^a-z]', '', clean)

    if not letters_only:
        return True, "No letters"

    # Count digits in original username
    digit_count = sum(1 for c in username if c.isdigit())
    if digit_count > 4:
        return True, f"Too many digits ({digit_count})"

    failed_tests = []

    # Test 1: Vowel Ratio
    vowel_count = sum(1 for c in letters_only if c in 'aeiou')
    vowel_count += sum(0.5 for c in letters_only if c == 'y')
    vowel_ratio = vowel_count / len(letters_only)

    if vowel_ratio < 0.25:
        failed_tests.append(f"Low vowel ratio ({vowel_ratio:.2f})")

    # Test 2: Consonant Run
    consonants = 0
    max_consonants = 0
    for c in letters_only:
        if c not in 'aeiouy':
            consonants += 1
            max_consonants = max(max_consonants, consonants)
        else:
            consonants = 0

    if max_consonants >= 5:
        failed_tests.append(f"Long consonant run ({max_consonants})")

    # Test 3: Common Bigrams
    # Common English bigrams (simplified list)
    common_bigrams = {
        'th', 'he', 'in', 'er', 'an', 're', 'ed', 'on', 'es', 'st',
        'en', 'at', 'to', 'nt', 'ha', 'nd', 'ou', 'ea', 'ng', 'as',
        'or', 'ti', 'is', 'et', 'it', 'ar', 'te', 'se', 'hi', 'of'
    }

    if len(letters_only) >= 2:
        bigrams = [letters_only[i:i+2] for i in range(len(letters_only)-1)]
        common_count = sum(1 for bg in bigrams if bg in common_bigrams)
        bigram_ratio = common_count / len(bigrams)

        if bigram_ratio < 0.15:
            failed_tests.append(f"Rare bigrams ({bigram_ratio:.2f})")

    # If 2+ tests failed, it's gibberish
    if len(failed_tests) >= 2:
        return True, "; ".join(failed_tests)

    return False, "Valid"