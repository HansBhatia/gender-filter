from openai import AsyncOpenAI
import os
import base64
from typing import Optional, Dict, List
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GenderDetector:
    """Clean async gender detector using OpenAI GPT-4o-mini."""

    def __init__(self, api_key: Optional[str] = None, max_concurrent: int = 50):
        self.model = "gpt-4o-mini"
        print(os.getenv("OPENAI_API_KEY"))
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = logging.getLogger(__name__)

    def encode_image(self, image_path: str) -> str:
        """Encode image file as base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    async def detect_gender(self, profile_pic_path: Optional[str], full_name: str, username: str) -> Dict:
        """
        Use GPT-4o-mini to detect gender from profile pic and name.
        Returns dict with is_male, reasoning, success.
        """
        async with self.semaphore:
            try:
                # If no profile pic, use name only
                if not profile_pic_path:
                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a gender detection assistant. Analyze the name to determine if the person appears to be male. Be concise. Return only: YES/NO and brief reason."
                            },
                            {
                                "role": "user",
                                "content": f"Is this person male based on the name? Name: '{full_name}', Username: '{username}'"
                            }
                        ],
                        temperature=0.0,
                        max_tokens=100
                    )
                else:
                    # Encode image
                    base64_image = self.encode_image(profile_pic_path)

                    response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a gender detection assistant. Analyze the profile picture and name to determine if the person appears to be male. Be concise. Return only: YES/NO and brief reason."
                            },
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Is this person male? Name: '{full_name}', Username: '{username}'"
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                                    }
                                ]
                            }
                        ],
                        temperature=0.0,
                        max_tokens=100
                    )

                content = response.choices[0].message.content.strip()
                is_male = content.upper().startswith("YES")

                return {
                    'is_male': is_male,
                    'reasoning': content,
                    'success': True
                }

            except Exception as e:
                self.logger.error(f"Error in gender detection for {username}: {e}")
                return {
                    'is_male': False,
                    'reasoning': f"Error: {e}",
                    'success': False
                }

    async def detect_gender_batch(self, profiles: List[Dict]) -> Dict:
        """
        Detect gender for multiple profiles concurrently.
        profiles: List of dicts with keys: username, full_name, profile_pic_path
        Returns summary dict with male_profiles, all_results, stats.
        """
        tasks = [
            self.detect_gender(
                profile.get('profile_pic_path'),
                profile.get('full_name', ''),
                profile.get('username', '')
            )
            for profile in profiles
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        male_profiles = []
        all_results = []
        success_count = 0
        failed_count = 0

        for i, result in enumerate(results):
            profile = profiles[i]
            username = profile.get('username', 'unknown')

            if isinstance(result, Exception):
                all_results.append({
                    'username': username,
                    'success': False,
                    'error': str(result)
                })
                failed_count += 1
            else:
                combined = {**profile, **result}
                all_results.append(combined)

                if result.get('success'):
                    success_count += 1
                    if result.get('is_male'):
                        male_profiles.append(combined)
                else:
                    failed_count += 1

        return {
            'male_profiles': male_profiles,
            'all_results': all_results,
            'success_count': success_count,
            'failed_count': failed_count,
            'male_count': len(male_profiles)
        }