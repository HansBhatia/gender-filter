import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import logging

from src.account_manager import AccountManager
from src.instagram_fetcher_v2 import InstagramFetcher
from src.gender_detector_v2 import GenderDetector
from src.gibberish_filter import is_gibberish
from src.business_filter import is_business_account


class GenderFilterPipeline:
    """Simplified pipeline with horizontal scaling via multiple IG accounts."""

    def __init__(
        self,
        accounts_file: str = "accounts.json",
        max_concurrent_ai: int = 50,
        batch_size: int = 100
    ):
        self.account_manager = AccountManager(accounts_file)
        self.gender_detector = GenderDetector(max_concurrent=max_concurrent_ai)
        self.batch_size = batch_size
        self.results_lock = Lock()
        self.fetchers = {}  # Cache fetchers by account_id to avoid re-login
        self.fetchers_lock = Lock()

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        self.logger.info(f"Pipeline initialized with {self.account_manager.count()} accounts")

    def _get_or_create_fetcher(self, account_config: Dict) -> InstagramFetcher:
        """Get cached fetcher or create new one (thread-safe)."""
        account_id = account_config['username']

        with self.fetchers_lock:
            if account_id not in self.fetchers:
                self.logger.info(f"Creating fetcher for account: {account_id}")
                self.fetchers[account_id] = InstagramFetcher(
                    username=account_config['username'],
                    password=account_config['password'],
                    otp=account_config.get('otp', ''),
                    proxy=account_config.get('proxy'),
                    account_id=account_id
                )
            return self.fetchers[account_id]

    def _fetch_ig_profile_worker(self, username: str, account_config: Dict) -> Dict:
        """Worker function to fetch a single IG profile."""
        try:
            fetcher = self._get_or_create_fetcher(account_config)
            result = fetcher.get_user_info(username)
            return result

        except Exception as e:
            self.logger.error(f"Worker error fetching {username}: {e}")
            return {
                'username': username,
                'exists': False,
                'error': str(e)
            }

    def fetch_ig_profiles_parallel(self, usernames: List[str]) -> Dict:
        """Fetch IG profiles using multiple accounts in parallel."""
        accounts = self.account_manager.get_all_accounts()
        num_workers = len(accounts)

        self.logger.info(f"Fetching {len(usernames)} profiles with {num_workers} workers")

        results = []
        failed = []

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []

            # Distribute usernames across accounts
            for i, username in enumerate(usernames):
                account = accounts[i % num_workers]
                future = executor.submit(self._fetch_ig_profile_worker, username, account)
                futures.append((future, username))

            # Collect results
            for future, username in futures:
                try:
                    result = future.result(timeout=60)
                    if result.get('exists'):
                        results.append(result)
                    else:
                        failed.append(username)
                except Exception as e:
                    self.logger.error(f"Future failed for {username}: {e}")
                    failed.append(username)

        return {
            'results': results,
            'failed': failed,
            'success_count': len(results),
            'failed_count': len(failed)
        }

    def _load_previously_processed(self, debug_file: str) -> set:
        """Load usernames that were successfully processed from debug log."""
        if not Path(debug_file).exists():
            return set()

        try:
            with open(debug_file, 'r') as f:
                debug_data = json.load(f)

            # Get all usernames that were successfully processed (not errors)
            processed = set()
            for result in debug_data.get('results', []):
                username = result.get('username')
                status = result.get('status', '')

                # Include any username that was fully processed (not IG errors)
                if username and not status.startswith('error_'):
                    processed.add(username)

            return processed
        except Exception as e:
            self.logger.warning(f"Could not load previous results from {debug_file}: {e}")
            return set()

    async def process_usernames(
        self,
        input_file: str,
        output_file: str = "male_usernames.txt",
        debug_file: str = "debug_log.json"
    ) -> Dict:
        """Main pipeline processing function."""

        self.logger.info("="*60)
        self.logger.info("GENDER FILTERING PIPELINE V2 - HORIZONTAL SCALING")
        self.logger.info("="*60)

        start_time = time.time()

        # Load usernames and deduplicate
        self.logger.info(f"Loading usernames from {input_file}")
        with open(input_file, 'r') as f:
            raw_usernames = [line.strip() for line in f if line.strip()]

        # Deduplicate input file
        usernames_before = len(raw_usernames)
        usernames = list(dict.fromkeys(raw_usernames))  # Preserves order while removing duplicates
        duplicates_removed = usernames_before - len(usernames)

        if duplicates_removed > 0:
            self.logger.info(f"Removed {duplicates_removed:,} duplicate entries from input file")

        # Skip previously processed usernames
        previously_processed = self._load_previously_processed(debug_file)
        if previously_processed:
            usernames_before_skip = len(usernames)
            usernames = [u for u in usernames if u not in previously_processed]
            skipped_count = usernames_before_skip - len(usernames)
            self.logger.info(f"Skipped {skipped_count:,} previously processed usernames")

        self.logger.info(f"Loaded {len(usernames):,} usernames to process")

        # Step 1: Filter gibberish and business accounts
        self.logger.info("\n🧹 Filtering gibberish and business usernames...")
        filter_start = time.time()

        valid_usernames = []
        gibberish_rejected = 0
        business_rejected = 0

        for username in usernames:
            # Check gibberish
            is_gib, gib_reason = is_gibberish(username)
            if is_gib:
                gibberish_rejected += 1
                continue

            # Check business
            is_biz, biz_reason = is_business_account(username)
            if is_biz:
                business_rejected += 1
                continue

            valid_usernames.append(username)

        filter_time = time.time() - filter_start
        self.logger.info(f"✅ {len(valid_usernames):,} valid usernames")
        self.logger.info(f"   Gibberish rejected: {gibberish_rejected:,}")
        self.logger.info(f"   Business rejected: {business_rejected:,}")
        self.logger.info(f"   Speed: {len(usernames) / filter_time:.1f} usernames/second")

        # Process in batches
        all_results = []
        all_male_usernames = []
        total_processed = 0
        verified_rejected = 0

        num_batches = (len(valid_usernames) + self.batch_size - 1) // self.batch_size

        for batch_idx in range(0, len(valid_usernames), self.batch_size):
            batch_usernames = valid_usernames[batch_idx:batch_idx + self.batch_size]
            batch_num = batch_idx // self.batch_size + 1

            self.logger.info(f"\n📦 Batch {batch_num}/{num_batches}: {len(batch_usernames)} usernames")

            # Step 2: Fetch Instagram profiles in parallel
            self.logger.info("   📱 Fetching Instagram profiles...")
            ig_start = time.time()

            ig_results = self.fetch_ig_profiles_parallel(batch_usernames)
            successful_profiles = ig_results['results']

            ig_time = time.time() - ig_start
            self.logger.info(f"   ✅ IG: {len(successful_profiles)}/{len(batch_usernames)} successful in {ig_time:.1f}s")
            self.logger.info(f"      Speed: {len(batch_usernames) / ig_time:.2f} profiles/second")

            if not successful_profiles:
                self.logger.warning("   ⚠️  No successful IG profiles, skipping batch")
                continue

            # Filter verified accounts
            unverified_profiles = []
            for profile in successful_profiles:
                if profile.get('is_verified'):
                    verified_rejected += 1
                    all_results.append({
                        'username': profile['username'],
                        'status': 'rejected_verified',
                        'reason': 'Verified account'
                    })
                else:
                    unverified_profiles.append(profile)

            if not unverified_profiles:
                self.logger.warning("   ⚠️  All profiles verified, skipping AI")
                continue

            # Step 3: AI Gender Detection
            self.logger.info(f"   🤖 AI gender detection on {len(unverified_profiles)} profiles...")
            ai_start = time.time()

            gender_results = await self.gender_detector.detect_gender_batch(unverified_profiles)

            ai_time = time.time() - ai_start
            self.logger.info(f"   ✅ AI: {gender_results['success_count']}/{len(unverified_profiles)} successful in {ai_time:.1f}s")
            self.logger.info(f"      Speed: {len(unverified_profiles) / ai_time:.2f} profiles/second")
            self.logger.info(f"      Male found: {gender_results['male_count']}")

            # Collect results
            male_usernames = [p['username'] for p in gender_results['male_profiles']]
            all_male_usernames.extend(male_usernames)

            # Create detailed results
            for result in gender_results['all_results']:
                status = 'accepted_male' if result.get('is_male') else 'rejected_not_male'
                all_results.append({
                    'username': result['username'],
                    'status': status,
                    'gender_detection': {
                        'is_male': result.get('is_male'),
                        'reasoning': result.get('reasoning'),
                        'success': result.get('success')
                    },
                    'instagram_data': {
                        'full_name': result.get('full_name'),
                        'profile_pic_path': result.get('profile_pic_path'),
                        'fetched_by': result.get('fetched_by')
                    }
                })

            # Add failed IG fetches
            for username in ig_results['failed']:
                all_results.append({
                    'username': username,
                    'status': 'error_instagram',
                    'reason': 'IG fetch failed'
                })

            total_processed += len(batch_usernames)
            progress = (batch_idx + len(batch_usernames)) / len(valid_usernames)
            self.logger.info(f"   📈 Progress: {progress:.1%} ({total_processed:,}/{len(valid_usernames):,})")

        # Final summary
        total_time = time.time() - start_time

        self.logger.info("\n" + "="*60)
        self.logger.info("🎉 PIPELINE COMPLETE")
        self.logger.info("="*60)
        self.logger.info(f"📊 SUMMARY:")
        self.logger.info(f"   Total usernames: {len(usernames):,}")
        self.logger.info(f"   Gibberish rejected: {gibberish_rejected:,}")
        self.logger.info(f"   Business rejected: {business_rejected:,}")
        self.logger.info(f"   Verified rejected: {verified_rejected:,}")
        self.logger.info(f"   Processed: {total_processed:,}")
        self.logger.info(f"   Male accounts found: {len(all_male_usernames):,}")

        if total_processed > 0:
            self.logger.info(f"   Success rate: {len(all_male_usernames) / total_processed:.1%}")

        self.logger.info(f"\n⏱️  PERFORMANCE:")
        self.logger.info(f"   Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        self.logger.info(f"   Overall speed: {len(usernames) / total_time:.1f} usernames/second")

        # Estimate for scale
        if total_time > 0:
            time_for_2m = (2_000_000 / (len(usernames) / total_time)) / 3600
            self.logger.info(f"\n📈 SCALE ESTIMATE:")
            self.logger.info(f"   2M usernames: ~{time_for_2m:.1f} hours at this speed")

        # Save results
        self.logger.info(f"\n💾 SAVING RESULTS:")

        # Append male usernames to output file
        with open(output_file, 'a') as f:
            for username in all_male_usernames:
                f.write(username + '\n')
        self.logger.info(f"   Male usernames appended to: {output_file}")

        # Load existing debug data and append new results
        existing_debug = {'summary': {}, 'results': []}
        if Path(debug_file).exists():
            try:
                with open(debug_file, 'r') as f:
                    existing_debug = json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load existing debug file: {e}")

        # Append new results
        existing_debug['results'].extend(all_results)

        # Update summary with cumulative stats
        new_summary = {
            'last_run': {
                'total_usernames': len(usernames),
                'gibberish_rejected': gibberish_rejected,
                'business_rejected': business_rejected,
                'verified_rejected': verified_rejected,
                'processed': total_processed,
                'male_found': len(all_male_usernames),
                'processing_time': total_time,
                'overall_speed': len(usernames) / total_time if total_time > 0 else 0
            },
            'cumulative': {
                'total_results': len(existing_debug['results']),
                'total_male': sum(1 for r in existing_debug['results'] if r.get('status') == 'accepted_male')
            }
        }
        existing_debug['summary'] = new_summary

        with open(debug_file, 'w') as f:
            json.dump(existing_debug, f, indent=2)
        self.logger.info(f"   Debug log updated: {debug_file} (now {len(existing_debug['results'])} total results)")

        return {
            'male_usernames': all_male_usernames,
            'total_processed': total_processed,
            'processing_time': total_time
        }

    def cleanup(self):
        """Close all Instagram fetchers and save sessions."""
        self.logger.info("\n🧹 Cleaning up fetchers...")
        with self.fetchers_lock:
            for account_id, fetcher in self.fetchers.items():
                try:
                    fetcher.close()
                    self.logger.info(f"   Closed fetcher for {account_id}")
                except Exception as e:
                    self.logger.warning(f"   Error closing fetcher {account_id}: {e}")
            self.fetchers.clear()


async def main():
    """Example usage."""
    pipeline = GenderFilterPipeline(
        accounts_file="accounts.json",
        max_concurrent_ai=50,
        batch_size=100
    )

    try:
        await pipeline.process_usernames(
            input_file="data/usernames.txt",
            output_file="output/male_usernames.txt",
            debug_file="output/debug_log.json"
        )
    finally:
        pipeline.cleanup()


if __name__ == "__main__":
    asyncio.run(main())