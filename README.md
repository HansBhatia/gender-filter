# Instagram Gender Filter Pipeline

Filters Instagram usernames to identify male accounts using AI-based gender detection.

## Setup

### 1. Install Dependencies
```bash
pipenv install
pipenv shell
```

### 2. Environment Variables
Create `env.py` with your credentials:
```python
INSTAGRAM_USERNAME = "your_instagram_username"
INSTAGRAM_PASSWORD = "your_instagram_password"
```

Set OpenAI API key:
```bash
export OPENAI_API_KEY="your_openai_api_key"
```

### 3. Instagram Session
First run creates `session.json` for future logins.

## Usage

### Input File
Create `usernames.txt` with one username per line:
```
username1
username2
username3
```

### Run Pipeline
```bash
python pipeline.py
```

## Pipeline Steps

1. **Gibberish Filter** - Removes usernames with low vowel ratio, long consonant runs, or rare bigrams
2. **Instagram Fetch** - Downloads profile data and profile pictures
3. **Verified Filter** - Skips verified accounts
4. **Gender Detection** - Uses GPT-4o-mini to analyze profile pic + name
5. **Output** - Saves male usernames to file

## Output Files

- `male_usernames.txt` - Clean list of detected male usernames
- `debug_log.json` - Detailed processing log for each username
- `images/` - Downloaded profile pictures

## Modules

- `gibberish_filter.py` - Username quality checks
- `instagram_fetcher.py` - Instagram API integration
- `gender_detector.py` - OpenAI gender detection
- `pipeline.py` - Main orchestrator

## Rate Limiting

Built-in delays (5-15 seconds) between Instagram requests to avoid rate limits.

---

## Legacy Tool (filter_usernames.py)
The original offline filter is available as a backup but not currently used in the main pipeline.
