from openai import OpenAI
import os
import base64
from typing import Optional, Dict

class GenderDetector:
    def __init__(self):
        self.model = "gpt-4o-mini"
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def encode_image(self, image_path: str) -> str:
        """Encode image file as base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def detect_gender(self, profile_pic_path: str, full_name: str, username: str) -> Dict:
        """
        Use GPT-4o-mini to detect gender from profile pic and name.
        Returns dict with is_male, confidence, reasoning
        """
        try:
            # If no profile pic, use name only
            if not profile_pic_path:
                response = self.client.chat.completions.create(
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

                response = self.client.chat.completions.create(
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
            print(f"Error in gender detection for {username}: {e}")
            return {
                'is_male': False,
                'reasoning': f"Error: {e}",
                'success': False
            }