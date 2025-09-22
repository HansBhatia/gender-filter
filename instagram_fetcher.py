from instagrapi import Client
from env import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
from typing import Optional, Dict
import time
import requests
from pathlib import Path

class InstagramFetcher:
    def __init__(self):
        self.cl = Client()
        if not Path("session.json").exists():
            self.cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            self.cl.dump_settings("session.json")
        else:
            self.cl.load_settings("session.json")
            self.cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        self.cl.delay_range = [5, 15]

        # Create images directory
        self.images_dir = Path("images")
        self.images_dir.mkdir(exist_ok=True)

    def get_user_info(self, username: str) -> Optional[Dict]:
        """
        Fetch user info from Instagram and download profile pic.
        Returns dict with is_verified, profile_pic_path, full_name
        Returns None if user not found or error.
        """
        try:
            user_info = self.cl.user_info_by_username(username)

            # Download profile pic
            profile_pic_path = None
            if user_info.profile_pic_url:
                try:
                    response = requests.get(str(user_info.profile_pic_url))
                    if response.status_code == 200:
                        profile_pic_path = self.images_dir / f"{username}_profile.jpg"
                        profile_pic_path.write_bytes(response.content)
                except Exception as e:
                    print(f"Error downloading profile pic for {username}: {e}")

            return {
                'username': username,
                'is_verified': user_info.is_verified,
                'profile_pic_path': str(profile_pic_path) if profile_pic_path else None,
                'full_name': user_info.full_name,
                'exists': True
            }
        except Exception as e:
            print(f"Error fetching {username}: {e}")
            return {
                'username': username,
                'exists': False,
                'error': str(e)
            }