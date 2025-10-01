# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Instagram gender filtering pipeline that processes usernames to identify male accounts using AI-based gender detection. The pipeline fetches Instagram profile data and uses OpenAI's GPT-4o-mini for gender detection based on profile pictures and names.

## Development Commands

### Setup and Run
```bash
# Install dependencies and activate environment
pipenv install
pipenv shell

# Run the main pipeline
python pipeline.py
```

### Required Environment Setup
- Create `env.py` with Instagram credentials (INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
- Set OpenAI API key: `export OPENAI_API_KEY="your_key"`

## Architecture

### Main Components
1. **pipeline.py** - Main orchestrator that coordinates the entire filtering process
2. **gibberish_filter.py** - Filters out low-quality usernames based on vowel ratio, consonant runs, and bigrams
3. **instagram_fetcher.py** - Handles Instagram API integration using instagrapi library
4. **gender_detector.py** - Uses OpenAI GPT-4o-mini to analyze profile pictures and names

### Data Flow
1. Reads usernames from `usernames.txt`
2. Filters gibberish usernames (vowel ratio, consonant patterns)
3. Fetches Instagram profile data and images
4. Skips verified accounts
5. Performs gender detection via OpenAI vision API
6. Outputs male usernames to `male_usernames.txt` and debug info to `debug_log.json`

### Key Implementation Details
- Rate limiting: 5-15 second delays between Instagram requests
- Session persistence: `session.json` stores Instagram login session
- Image storage: Profile pictures saved to `images/` directory
- Batch processing with detailed debug logging for each username

## Dependencies
- **instagrapi** - Instagram private API client
- **openai** - GPT-4o-mini for gender detection
- **gender-guesser** - Name-based gender detection (used in legacy filter_usernames.py)
- **seleniumbase** - Browser automation (alternative fetching method)
- **rapidfuzz** - Fuzzy string matching