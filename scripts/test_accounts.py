"""Test script to verify Instagram accounts in accounts.json are working."""

import json
import sys
from pathlib import Path
import pyotp

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.instagram_fetcher_v2 import InstagramFetcher


def test_accounts():
    """Test all Instagram accounts in accounts.json."""

    print("="*60)
    print("TESTING INSTAGRAM ACCOUNTS")
    print("="*60)

    # Load accounts
    with open('accounts.json', 'r') as f:
        accounts = json.load(f)

    print(f"\nFound {len(accounts)} accounts to test\n")

    results = []

    for idx, account in enumerate(accounts):
        username = account['username']
        print(f"\n[{idx}] Testing account: {username}")
        print("-" * 40)

        try:
            otp = pyotp.TOTP(account.get('otp_seed', '')).now()
            # Initialize fetcher
            fetcher = InstagramFetcher(
                username=account['username'],
                password=account['password'],
                otp=otp,
                proxy=account.get('proxy'),
                account_id=account['username']
            )

            # Test by fetching a known profile (Instagram's own account)
            print(f"   Attempting to fetch test profile...")
            test_result = fetcher.user_info_by_username_v1("instagram")

            if test_result:
                print(f"   ✅ SUCCESS: Account is working")
                print(f"   Profile fetched: @{test_result.username}")
                print(f"   Full name: {test_result.full_name}")
                results.append({
                    'index': idx,
                    'username': username,
                    'status': 'success',
                    'proxy': account.get('proxy', 'none')
                })
            else:
                print(f"   ❌ FAILED: Could not fetch test profile")
                results.append({
                    'index': idx,
                    'username': username,
                    'status': 'failed',
                    'error': 'Profile fetch failed',
                    'proxy': account.get('proxy', 'none')
                })

            fetcher.close()

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append({
                'index': idx,
                'username': username,
                'status': 'error',
                'error': str(e),
                'proxy': account.get('proxy', 'none')
            })

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] != 'success']

    print(f"\nTotal accounts: {len(results)}")
    print(f"✅ Working: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")

    if successful:
        print(f"\n✅ Working accounts:")
        for r in successful:
            print(f"   [{r['index']}] {r['username']} (proxy: {r['proxy'][:30]}...)")

    if failed:
        print(f"\n❌ Failed accounts:")
        for r in failed:
            error = r.get('error', 'Unknown error')
            print(f"   [{r['index']}] {r['username']}: {error}")

    return results


if __name__ == "__main__":
    test_accounts()