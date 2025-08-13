Username Filter — Quick Start
This tool filters a large list of usernames (300k–500k) to keep only likely male personal usernames, removing business accounts and female/ambiguous names — all offline with no API costs.

1. Install & Activate Environment

   ```bash
   pipenv install
   pipenv shell
   ```

   This will install the required dependencies from Pipfile.

2. Prepare Input
   Place your usernames in a file called:

   ```
   usernames.txt
   (one username per line)
   ```

3. Run the Filter
   ```bash
   python filter_usernames.py
   ```
4. Results
   The script will create:

filtered_male.txt — kept usernames

rejected_business.txt — removed business-like usernames

rejected_female_or_ambiguous.txt — removed female/unknown/androgynous usernames

stats.txt — summary counts

That’s it — just install, activate, add your input file, and run.
