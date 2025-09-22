import json
from pathlib import Path
from gibberish_filter import is_gibberish
from instagram_fetcher import InstagramFetcher
from gender_detector import GenderDetector
import time

def process_usernames(input_file: str, output_file: str = "male_usernames.txt", debug_file: str = "debug_log.json"):
    """
    Main pipeline to process Instagram usernames and find male accounts.
    """

    # Load usernames
    usernames = []
    with open(input_file, 'r') as f:
        usernames = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(usernames)} usernames")

    # Initialize modules
    ig_fetcher = InstagramFetcher()
    gender_detector = GenderDetector()

    # Process results
    results = []
    male_usernames = []

    for idx, username in enumerate(usernames):
        print(f"\n[{idx+1}/{len(usernames)}] Processing: {username}")

        result = {'username': username}

        # Step 1: Check for gibberish
        is_gib, gib_reason = is_gibberish(username)
        if is_gib:
            result['status'] = 'rejected_gibberish'
            result['reason'] = gib_reason
            print(f"  ❌ Gibberish: {gib_reason}")
            results.append(result)
            continue

        # Step 2: Fetch Instagram data
        print(f"  📱 Fetching Instagram data...")
        ig_data = ig_fetcher.get_user_info(username)

        if not ig_data or not ig_data.get('exists'):
            result['status'] = 'error_instagram'
            result['reason'] = ig_data.get('error', 'User not found') if ig_data else 'Fetch failed'
            print(f"  ❌ Instagram error: {result['reason']}")
            results.append(result)
            continue

        result['instagram_data'] = ig_data

        # Step 3: Check if verified (skip verified users)
        if ig_data.get('is_verified'):
            result['status'] = 'rejected_verified'
            result['reason'] = 'Verified account'
            print(f"  ❌ Verified account")
            results.append(result)
            continue

        # Step 4: Gender detection
        print(f"  🔍 Detecting gender...")
        gender_result = gender_detector.detect_gender(
            ig_data.get('profile_pic_path'),
            ig_data['full_name'],
            username
        )

        result['gender_detection'] = gender_result

        if gender_result.get('success') and gender_result.get('is_male'):
            result['status'] = 'accepted_male'
            male_usernames.append(username)
            print(f"  ✅ Male detected: {gender_result['reasoning']}")
        else:
            result['status'] = 'rejected_not_male'
            result['reason'] = gender_result.get('reasoning', 'Not detected as male')
            print(f"  ❌ Not male: {result['reason']}")

        results.append(result)

        # Small delay between users
        time.sleep(2)

    # Save results
    with open(output_file, 'w') as f:
        for username in male_usernames:
            f.write(username + '\n')

    with open(debug_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Total processed: {len(usernames)}")
    print(f"Male accounts found: {len(male_usernames)}")
    print(f"Gibberish rejected: {sum(1 for r in results if r.get('status') == 'rejected_gibberish')}")
    print(f"Instagram errors: {sum(1 for r in results if r.get('status') == 'error_instagram')}")
    print(f"Verified rejected: {sum(1 for r in results if r.get('status') == 'rejected_verified')}")
    print(f"Not male: {sum(1 for r in results if r.get('status') == 'rejected_not_male')}")
    print(f"\nMale usernames saved to: {output_file}")
    print(f"Debug log saved to: {debug_file}")

if __name__ == "__main__":
    process_usernames("usernames.txt")