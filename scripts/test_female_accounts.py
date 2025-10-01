"""Test script to verify female accounts are correctly identified."""

import asyncio
import json
from src.instagram_fetcher_v2 import InstagramFetcher
from src.gender_detector_v2 import GenderDetector

# Test cases - all should be identified as female
FEMALE_TEST_ACCOUNTS = [
    "wswrg",      # Wendy Wallberg
    "flywon",     # EriCa
    "dnsk0206",   # Dani Sánchez
    "mjxk_25",    # Mariana Gomez
]


async def test_female_detection():
    """Test that known female accounts are correctly identified."""

    print("="*60)
    print("TESTING FEMALE ACCOUNT DETECTION")
    print("="*60)

    # Load account 0 from accounts.json
    with open('accounts.json', 'r') as f:
        accounts = json.load(f)

    account = accounts[0]
    print(f"\n🔑 Using account: {account['username']}")

    # Initialize
    fetcher = InstagramFetcher(
        username=account['username'],
        password=account['password'],
        otp=account.get('otp_seed', ''),
        proxy=account.get('proxy'),
        account_id=account['username']
    )

    detector = GenderDetector(max_concurrent=10)

    # Fetch profiles
    print(f"\n📱 Fetching {len(FEMALE_TEST_ACCOUNTS)} profiles...")
    profiles = []

    for username in FEMALE_TEST_ACCOUNTS:
        print(f"   Fetching @{username}...")
        try:
            result = fetcher.get_user_info(username)
            if result.get('exists'):
                profiles.append(result)
                print(f"   ✅ @{username}: {result.get('full_name', 'N/A')}")
            else:
                print(f"   ❌ @{username}: Profile not found")
        except Exception as e:
            print(f"   ❌ @{username}: Error - {e}")

    fetcher.close()

    if not profiles:
        print("\n❌ No profiles fetched successfully")
        return

    # Run gender detection
    print(f"\n🤖 Running AI gender detection on {len(profiles)} profiles...")
    results = await detector.detect_gender_batch(profiles)

    # Analyze results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)

    errors = []

    for result in results['all_results']:
        username = result['username']
        is_male = result.get('is_male', False)
        reasoning = result.get('reasoning', 'N/A')
        success = result.get('success', False)

        status = "✅ CORRECT" if not is_male else "❌ INCORRECT (detected as male)"

        print(f"\n@{username}:")
        print(f"  Detection: {'Male' if is_male else 'Female'} {status}")
        print(f"  Reasoning: {reasoning}")
        print(f"  Success: {success}")

        if is_male:
            errors.append({
                'username': username,
                'full_name': result.get('full_name'),
                'reasoning': reasoning
            })

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    correct = len(profiles) - len(errors)
    print(f"Total tested: {len(profiles)}")
    print(f"Correct (female): {correct}")
    print(f"Incorrect (male): {len(errors)}")
    print(f"Accuracy: {correct/len(profiles)*100:.1f}%")

    if errors:
        print("\n❌ FALSE POSITIVES (females incorrectly detected as male):")
        for error in errors:
            print(f"  - @{error['username']} ({error['full_name']})")
            print(f"    Reason: {error['reasoning']}")
    else:
        print("\n✅ All female accounts correctly identified!")

    return {
        'total': len(profiles),
        'correct': correct,
        'errors': errors
    }


if __name__ == "__main__":
    asyncio.run(test_female_detection())