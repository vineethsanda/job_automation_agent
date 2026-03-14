"""Stealth browser utilities for LinkedIn automation with human behavior simulation."""

import asyncio
import random
from typing import Optional, Dict, List
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from loguru import logger


class StealthBrowser:
    """Playwright browser with stealth patches and human behavior simulation."""

    def __init__(self, session_dir: str = "/tmp/linkedin_session"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def launch(self) -> None:
        """Launch browser with stealth options."""
        try:
            playwright = await async_playwright().start()

            # Launch with stealth options
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--single-process=false",
                    "--no-first-run",
                ],
            )

            # Create context with stealth patches
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="America/New_York",
            )

            # Load session cookies if available
            await self._load_cookies()

            self.page = await self.context.new_page()

            # Inject stealth scripts
            await self._inject_stealth_scripts()

            logger.info("Stealth browser launched")

        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise

    async def _inject_stealth_scripts(self) -> None:
        """Inject stealth scripts to hide automation."""
        if not self.page:
            return

        # Disable webdriver property
        await self.page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            """
        )

    async def goto_with_delay(self, url: str) -> None:
        """Navigate to URL with randomized delay."""
        if not self.page:
            raise RuntimeError("Browser not initialized")

        delay = random.uniform(2, 8)
        await asyncio.sleep(delay)

        try:
            await self.page.goto(url, wait_until="networkidle")
            logger.debug(f"Navigated to {url}")
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise

    async def human_scroll(self, page_height: int = 3000) -> None:
        """Scroll page with human-like behavior."""
        if not self.page:
            return

        current_scroll = 0
        target_scroll = page_height

        while current_scroll < target_scroll:
            # Random scroll amount
            scroll_amount = random.randint(200, 500)
            current_scroll += scroll_amount

            await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")

            # Random pause between scrolls
            pause = random.uniform(0.5, 2.5)
            await asyncio.sleep(pause)

            logger.debug(f"Scrolled {scroll_amount}px (total: {current_scroll}px)")

    async def human_click(self, selector: str) -> None:
        """Click element with human-like delays."""
        if not self.page:
            return

        try:
            # Random delay before click
            await asyncio.sleep(random.uniform(0.5, 1.5))

            # Click with random offset
            element = await self.page.query_selector(selector)
            if element:
                await element.scroll_into_view_if_needed()
                await asyncio.sleep(random.uniform(0.2, 0.5))

                # Simulate mouse movement
                box = await element.bounding_box()
                if box:
                    offset_x = random.randint(5, int(box["width"] - 5))
                    offset_y = random.randint(5, int(box["height"] - 5))

                    await self.page.mouse.move(
                        box["x"] + offset_x, box["y"] + offset_y
                    )
                    await asyncio.sleep(random.uniform(0.1, 0.3))

                await element.click()
                logger.debug(f"Clicked element: {selector}")
            else:
                logger.warning(f"Element not found: {selector}")
        except Exception as e:
            logger.error(f"Failed to click element {selector}: {e}")

    async def human_type(self, selector: str, text: str) -> None:
        """Type text with human-like delays."""
        if not self.page:
            return

        try:
            await self.page.fill(selector, "")
            await asyncio.sleep(random.uniform(0.2, 0.5))

            # Type with random delays between characters
            for char in text:
                await self.page.type(selector, char)
                await asyncio.sleep(random.uniform(0.02, 0.1))

            logger.debug(f"Typed text in {selector}")
        except Exception as e:
            logger.error(f"Failed to type in {selector}: {e}")

    async def _load_cookies(self) -> None:
        """Load session cookies from file."""
        if not self.context:
            return

        cookie_file = self.session_dir / "cookies.json"
        if cookie_file.exists():
            try:
                import json
                with open(cookie_file, "r") as f:
                    cookies = json.load(f)
                await self.context.add_cookies(cookies)
                logger.info(f"Loaded {len(cookies)} cookies from session")
            except Exception as e:
                logger.error(f"Failed to load cookies: {e}")

    async def save_cookies(self) -> None:
        """Save session cookies to file."""
        if not self.context:
            return

        try:
            import json
            cookies = await self.context.cookies()
            cookie_file = self.session_dir / "cookies.json"

            with open(cookie_file, "w") as f:
                json.dump(cookies, f)

            # Set restrictive permissions
            import os
            os.chmod(cookie_file, 0o600)

            logger.info(f"Saved {len(cookies)} cookies to session")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

    async def close(self) -> None:
        """Close browser and cleanup."""
        try:
            if self.page:
                await self.save_cookies()
                await self.page.close()

            if self.context:
                await self.context.close()

            if self.browser:
                await self.browser.close()

            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    async def wait_for_selector(self, selector: str, timeout: int = 10000) -> bool:
        """Wait for element to appear on page."""
        if not self.page:
            return False

        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    async def get_content(self) -> Optional[str]:
        """Get current page content."""
        if not self.page:
            return None

        try:
            return await self.page.content()
        except Exception as e:
            logger.error(f"Failed to get page content: {e}")
            return None
