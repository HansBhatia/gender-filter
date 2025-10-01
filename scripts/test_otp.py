#!/usr/bin/env python3
"""
Test OTP generation using pyotp.
Usage: python test_otp.py <seed>
"""

import sys
import pyotp


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_otp.py <seed>")
        sys.exit(1)

    seed = sys.argv[1]

    # Create TOTP object with the seed
    totp = pyotp.TOTP(seed)

    # Generate current OTP code
    otp_code = totp.now()

    print(f"Current OTP code: {otp_code}")


if __name__ == "__main__":
    main()