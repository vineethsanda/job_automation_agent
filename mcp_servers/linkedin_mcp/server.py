"""LinkedIn MCP Server - Job discovery and recruiter contact via Model Context Protocol."""

import os
import asyncio
from typing import Optional
from mcp.server.fastmcp import FastMCP
from loguru import logger

from utils.stealth_browser import StealthBrowser
from utils.cookie_store import CookieStore
from tools.fetch_posts import fetch_job_posts
from tools.extract_recruiter_email import extract_recruiter_email
from tools.session_manager import manage_session


# Initialize FastMCP server
mcp = FastMCP("linkedin_mcp")

# Global state
browser: Optional[StealthBrowser] = None
cookie_store: Optional[CookieStore] = None
LINKEDIN_EMAIL: Optional[str] = None
LINKEDIN_PASSWORD: Optional[str] = None
LAST_RUN: Optional[float] = None
RUN_INTERVAL = 20 * 60  # 20-minute minimum between runs


async def ensure_browser() -> bool:
    """Ensure browser is initialized and logged in."""
    global browser

    try:
        if not browser:
            browser = StealthBrowser()
            await browser.launch()

        # Check if session has valid cookies
        if cookie_store:
            cookies = cookie_store.load_cookies()
            if not cookies:
                logger.warning("No valid session cookies, login required")
                return False

        return True

    except Exception as e:
        logger.error(f"Failed to ensure browser: {e}")
        return False


async def check_rate_limit() -> bool:
    """Check if minimum interval between runs has elapsed."""
    global LAST_RUN

    import time

    current_time = time.time()
    if LAST_RUN and (current_time - LAST_RUN) < RUN_INTERVAL:
        remaining = int(RUN_INTERVAL - (current_time - LAST_RUN))
        logger.warning(
            f"Rate limit: {remaining}s remaining until next run"
        )
        return False

    LAST_RUN = current_time
    return True


@mcp.tool()
async def fetch_jobs(
    search_query: str = "Job postings",
    max_results: int = 10,
) -> dict:
    """
    Fetch job postings from LinkedIn.

    Args:
        search_query: Job search query
        max_results: Maximum results (default: 10)

    Returns:
        Dictionary with job posts
    """
    if not await check_rate_limit():
        return {
            "status": "rate_limited",
            "error": "Minimum 20-minute interval between runs",
        }

    if not await ensure_browser() or not browser:
        return {
            "status": "error",
            "error": "Browser not available",
        }

    return await fetch_job_posts(browser, search_query, max_results)


@mcp.tool()
async def get_recruiter_contact(profile_url: str) -> dict:
    """
    Extract recruiter contact information from LinkedIn profile.

    Args:
        profile_url: LinkedIn profile URL

    Returns:
        Dictionary with contact information
    """
    if not await ensure_browser() or not browser:
        return {
            "status": "error",
            "error": "Browser not available",
        }

    return await extract_recruiter_email(browser, profile_url)


@mcp.tool()
async def session_action(action: str = "status") -> dict:
    """
    Manage LinkedIn session.

    Args:
        action: 'status', 'save', 'load', or 'clear'

    Returns:
        Dictionary with action result
    """
    if not cookie_store:
        return {
            "status": "error",
            "error": "Cookie store not initialized",
        }

    return await manage_session(cookie_store, action)


async def initialize() -> bool:
    """Initialize LinkedIn MCP server."""
    global browser, cookie_store, LINKEDIN_EMAIL, LINKEDIN_PASSWORD

    try:
        LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
        LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

        if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
            logger.warning(
                "LinkedIn credentials not provided (LINKEDIN_EMAIL, LINKEDIN_PASSWORD). "
                "Session login will be required."
            )

        cookie_store = CookieStore()
        logger.info("LinkedIn MCP Server initialized")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize LinkedIn server: {e}")
        return False


@mcp.on_startup
async def on_startup() -> None:
    """Initialize server on startup."""
    logger.info("LinkedIn MCP Server starting...")
    await initialize()


@mcp.on_shutdown
async def on_shutdown() -> None:
    """Cleanup on shutdown."""
    global browser
    if browser:
        await browser.close()
        logger.info("Browser closed")


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        "logs/linkedin_mcp.log",
        rotation="10 MB",
        retention=3,
        level="DEBUG",
    )

    logger.info("Starting LinkedIn MCP Server...")
    mcp.run()
