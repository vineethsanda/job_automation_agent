"""Cookie storage management for LinkedIn session persistence."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger


class CookieStore:
    """Manage plaintext cookie storage for LinkedIn sessions."""

    def __init__(self, storage_dir: str = "/tmp/linkedin_session"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.cookie_file = self.storage_dir / "cookies.json"

    def save_cookies(self, cookies: List[Dict]) -> bool:
        """Save cookies to plaintext JSON file."""
        try:
            with open(self.cookie_file, "w") as f:
                json.dump(cookies, f, indent=2)

            # Set restrictive permissions (600 = rw-------)
            os.chmod(self.cookie_file, 0o600)
            logger.info(f"Saved {len(cookies)} cookies to {self.cookie_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            return False

    def load_cookies(self) -> Optional[List[Dict]]:
        """Load cookies from plaintext JSON file."""
        try:
            if not self.cookie_file.exists():
                logger.debug("Cookie file not found")
                return None

            with open(self.cookie_file, "r") as f:
                cookies = json.load(f)

            logger.info(f"Loaded {len(cookies)} cookies from {self.cookie_file}")
            return cookies

        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return None

    def clear_cookies(self) -> bool:
        """Delete cookie file."""
        try:
            if self.cookie_file.exists():
                self.cookie_file.unlink()
                logger.info("Cookies cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cookies: {e}")
            return False

    def get_cookie_names(self) -> List[str]:
        """Get list of all cookie names."""
        cookies = self.load_cookies()
        if not cookies:
            return []

        return [c.get("name", "") for c in cookies if c.get("name")]

    def get_session_status(self) -> Dict:
        """Get cookie store status."""
        cookies = self.load_cookies()
        return {
            "cookie_file": str(self.cookie_file),
            "exists": self.cookie_file.exists(),
            "count": len(cookies) if cookies else 0,
            "permissions": oct(os.stat(self.cookie_file).st_mode)[-3:]
            if self.cookie_file.exists()
            else None,
        }
