from instagrapi import Client
from typing import Optional, Dict
import time
import requests
from pathlib import Path
import logging

class InstagramFetcher:
    """Clean Instagram fetcher using instagrapi with proxy support."""

    def __init__(self, username: str, password: str, otp: str, proxy: Optional[str] = None, account_id: str = "default"):
        self.username = username
        self.account_id = account_id
        self.logger = logging.getLogger(__name__)

        # Setup client with proxy
        self.cl = Client()
        if proxy:
            self.cl.set_proxy(f"http://{proxy}")
            self.logger.info(f"Account {account_id}: Using proxy {proxy}")

        # Setup session management
        self.sessions_dir = Path("sessions")
        self.sessions_dir.mkdir(exist_ok=True)
        self.session_file = self.sessions_dir / f"session_{account_id}.json"

        # Login with session persistence
        self._login(username, password, otp)

        # Set rate limiting
        self.cl.delay_range = [3, 7]

        # Create images directory
        self.images_dir = Path("images")
        self.images_dir.mkdir(exist_ok=True)

    def _login(self, username: str, password: str, otp: str):
        """Login with session persistence."""
        try:
            if self.session_file.exists():
                self.logger.info(f"Account {self.account_id}: Loading existing session")
                self.cl.load_settings(str(self.session_file))
                # Relogin with loaded session (no OTP needed)
                self.cl.login(username, password)
                self.logger.info(f"Account {self.account_id}: Reused existing session")
            else:
                self.logger.info(f"Account {self.account_id}: Creating new session")
                self.cl.login(username, password, verification_code=otp)
                self.cl.dump_settings(str(self.session_file))
                self.logger.info(f"Account {self.account_id}: Created new session")
        except Exception as e:
            self.logger.error(f"Account {self.account_id}: Login failed - {e}")
            # Try fresh login with OTP on failure
            try:
                self.logger.info(f"Account {self.account_id}: Attempting fresh login")
                self.cl.login(username, password, verification_code=otp)
                self.cl.dump_settings(str(self.session_file))
                self.logger.info(f"Account {self.account_id}: Fresh login successful")
            except Exception as e2:
                self.logger.error(f"Account {self.account_id}: Fresh login also failed - {e2}")
                raise

    def user_info_by_username_v1(self, username: str) -> Optional[Dict]:
        """
        Fetch user info from Instagram and download profile pic.
        Returns dict with is_verified, profile_pic_path, full_name, exists.
        Returns None if user not found or error.
        """
        return self.cl.user_info_by_username_v1(username)

    def get_user_info(self, username: str) -> Optional[Dict]:
        """
        Fetch user info from Instagram and download profile pic.
        Returns dict with is_verified, profile_pic_path, full_name, exists.
        Returns None if user not found or error.
        """
        try:
            user_info = self.cl.user_info_by_username_v1(username)

            # Download profile pic
            profile_pic_path = None
            if user_info.profile_pic_url:
                try:
                    response = requests.get(str(user_info.profile_pic_url), timeout=10)
                    if response.status_code == 200:
                        profile_pic_path = self.images_dir / f"{username}_profile.jpg"
                        profile_pic_path.write_bytes(response.content)
                except Exception as e:
                    self.logger.warning(f"Error downloading profile pic for {username}: {e}")

            return {
                'username': username,
                'is_verified': user_info.is_verified,
                'profile_pic_path': str(profile_pic_path) if profile_pic_path else None,
                'full_name': user_info.full_name,
                'exists': True,
                'fetched_by': self.account_id
            }
        except Exception as e:
            self.logger.warning(f"Error fetching {username}: {e}")
            return {
                'username': username,
                'exists': False,
                'error': str(e),
                'fetched_by': self.account_id
            }

    def close(self):
        """Save session without logging out to preserve credentials."""
        try:
            # Save session state but DON'T logout to keep session valid
            self.cl.dump_settings(str(self.session_file))
        except Exception as e:
            self.logger.warning(f"Account {self.account_id}: Failed to save session - {e}")