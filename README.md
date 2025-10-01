# Instagram Gender Filter Pipeline V2

Simplified, modular Instagram gender filtering pipeline with horizontal scaling via multiple accounts.

## Project Structure

```
gender-filter/
├── src/                           # Core modules
│   ├── account_manager.py         # Multi-account management with OTP
│   ├── instagram_fetcher_v2.py    # Instagram fetcher with proxy support
│   ├── gender_detector_v2.py      # Async OpenAI gender detection
│   ├── gibberish_filter.py        # Username quality filter
│   └── business_filter.py         # Business keyword filter
├── data/                          # Input data
│   └── usernames.txt              # Input usernames (one per line)
├── output/                        # Output files (auto-generated)
├── sessions/                      # IG session files (auto-generated)
├── images/                        # Profile pictures (auto-generated)
├── main.py                        # Main pipeline script
├── accounts.example.json          # Account config template
└── README.md
```

## Setup

### 1. Install Dependencies

```bash
pipenv install pyotp  # Add if not already in Pipfile
pipenv shell
```

### 2. Configure Accounts

Create `accounts.json` based on `accounts.example.json`:

```json
[
  {
    "username": "your_ig_username_1",
    "password": "your_password_1",
    "otp_seed": "your_otp_seed_1",
    "proxy": "username:password@proxy-host:port"
  },
  {
    "username": "your_ig_username_2",
    "password": "your_password_2",
    "otp_seed": "your_otp_seed_2",
    "proxy": "username:password@proxy-host:port"
  }
]
```

**Important:**
- Each account should have its own proxy in the same geographic region
- Using the same proxy for multiple accounts or mixing regions can lead to Instagram blocks
- The pipeline will distribute work across all accounts

### 3. Verify Configuration

Before running the pipeline, test your proxies and accounts:

**Test Proxies:**
```bash
# Test all proxies from accounts.json
python scripts/test_proxy.py

# Test a specific account's proxy (by index)
python scripts/test_proxy.py 0
```

This verifies each proxy is working and shows its geographic location.

**Test Instagram Accounts:**
```bash
python scripts/test_accounts.py
```

This logs into each Instagram account and attempts to fetch a test profile. All accounts should show ✅ SUCCESS before running the main pipeline.

### 4. Set OpenAI API Key

```bash
export OPENAI_API_KEY="your_openai_api_key"
```

### 5. Prepare Input

Create `data/usernames.txt` with one username per line:

```
username1
username2
username3
```

## Usage

```bash
python main.py
```

The pipeline will:
1. Filter gibberish usernames
2. Filter business accounts (coach, hotel, agency, etc.)
3. Fetch Instagram profiles in parallel using multiple accounts
4. Skip verified accounts
5. Detect gender using AI on profile pictures and names
6. Output male usernames to `output/male_usernames.txt`

## Configuration

Edit `main.py` main function:

```python
pipeline = GenderFilterPipeline(
    accounts_file="accounts.json",     # Path to accounts config
    max_concurrent_ai=50,               # Concurrent OpenAI requests
    batch_size=100                      # Usernames per batch
)

await pipeline.process_usernames(
    input_file="data/usernames.txt",
    output_file="output/male_usernames.txt",
    debug_file="output/debug_log.json"
)
```

## Output

- `output/male_usernames.txt` - List of detected male usernames
- `output/debug_log.json` - Detailed results for each username
- `sessions/` - Instagram session files (auto-managed)
- `images/` - Downloaded profile pictures

## Horizontal Scaling

The pipeline distributes work across all configured accounts:
- Each account can operate independently with its own proxy
- Work is distributed round-robin across accounts
- Slower, more reliable approach vs browser automation

## Key Features

- **Multi-account support** with OTP and proxy per account
- **Session persistence** to avoid repeated logins
- **Rate limiting** built-in (3-7 second delays)
- **Parallel execution** across multiple accounts
- **Async AI processing** for speed
- **Comprehensive logging** and error handling
- **Clean modular design** like `instagram_fetcher.py`

---

## Notes

- The pipeline uses prefilters (gibberish + business) before hitting Instagram API
- Business filter catches keywords like: coach, hotel, agency, restaurant, consulting, yacht, club, etc.
- Each account maintains its own session to avoid repeated logins
- Rate limiting (3-7 seconds) is built-in to avoid Instagram blocks
