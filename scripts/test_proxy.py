#!/usr/bin/env python3
"""
Test if proxies from accounts.json work by making HTTP/HTTPS requests through them.
Usage: python test_proxy.py [account_index]
Example: python test_proxy.py 0  # Test first account's proxy
         python test_proxy.py     # Test all proxies
"""

import sys
import json
import requests
from pathlib import Path
from requests.exceptions import ProxyError, Timeout, RequestException


def format_proxy_url(proxy_string):
    """Convert username:password@host:port to http://username:password@host:port"""
    if not proxy_string.startswith('http'):
        return f'http://{proxy_string}'
    return proxy_string


def test_proxy(proxy_string, account_username=None, timeout=10):
    """Test if a proxy works by making requests to test endpoints."""

    proxy_url = format_proxy_url(proxy_string)

    proxies = {
        'http': proxy_url,
        'https': proxy_url,
    }

    test_urls = [
        ('http://httpbin.org/ip', 'HTTP'),
        ('https://httpbin.org/ip', 'HTTPS'),
    ]

    header = f"Account: {account_username}" if account_username else f"Proxy: {proxy_string}"
    print(f"\n{header}")
    print("=" * 50)

    results = []

    for url, protocol in test_urls:
        try:
            print(f"Testing {protocol}...", end=" ")
            response = requests.get(url, proxies=proxies, timeout=timeout)

            if response.status_code == 200:
                ip_data = response.json()
                print(f"✓ Works! IP: {ip_data.get('origin', 'unknown')}")
                results.append(True)
            else:
                print(f"✗ Failed (status {response.status_code})")
                results.append(False)

        except ProxyError as e:
            print(f"✗ Proxy error: {str(e)[:60]}")
            results.append(False)
        except Timeout:
            print(f"✗ Timeout ({timeout}s)")
            results.append(False)
        except RequestException as e:
            print(f"✗ Error: {str(e)[:60]}")
            results.append(False)

    if all(results):
        print("✓ Proxy is working for all protocols!")
        return 0
    elif any(results):
        print("⚠ Proxy partially working")
        return 1
    else:
        print("✗ Proxy is not working")
        return 2


def load_accounts(filepath='accounts.json'):
    """Load accounts from JSON file."""
    accounts_path = Path(__file__).parent.parent / filepath

    if not accounts_path.exists():
        print(f"Error: {filepath} not found at {accounts_path}")
        sys.exit(1)

    with open(accounts_path, 'r') as f:
        return json.load(f)


if __name__ == "__main__":
    accounts = load_accounts()

    if len(sys.argv) == 2:
        # Test specific account
        try:
            index = int(sys.argv[1])
            if index < 0 or index >= len(accounts):
                print(f"Error: Account index {index} out of range (0-{len(accounts)-1})")
                sys.exit(1)

            account = accounts[index]
            exit_code = test_proxy(account['proxy'], account['username'])
            sys.exit(exit_code)
        except ValueError:
            print("Error: Account index must be a number")
            sys.exit(1)
    else:
        # Test all accounts
        print(f"Testing {len(accounts)} proxy/proxies from accounts.json")
        results = []

        for i, account in enumerate(accounts):
            result = test_proxy(account['proxy'], account['username'])
            results.append((i, account['username'], result))

        # Summary
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)

        working = sum(1 for _, _, r in results if r == 0)
        partial = sum(1 for _, _, r in results if r == 1)
        failed = sum(1 for _, _, r in results if r == 2)

        print(f"✓ Working: {working}/{len(accounts)}")
        print(f"⚠ Partial: {partial}/{len(accounts)}")
        print(f"✗ Failed: {failed}/{len(accounts)}")

        if failed > 0:
            print("\nFailed accounts:")
            for i, username, result in results:
                if result == 2:
                    print(f"  [{i}] {username}")

        sys.exit(0 if working == len(accounts) else 1)