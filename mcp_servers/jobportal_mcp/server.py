"""Job Portal MCP Server - Handle job portal automation via Model Context Protocol."""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from loguru import logger
from playwright.async_api import async_playwright, Page

from utils.form_filler import FormFiller
from utils.otp_handler import OTPHandler
from tools.create_account import create_account
from tools.fill_application import fill_application
from tools.handle_redirect import handle_redirect


# Initialize FastMCP server
mcp = FastMCP("jobportal_mcp")

# Global state
page: Optional[Page] = None
form_filler: Optional[FormFiller] = None
metadata_file: Optional[Path] = None


async def get_metadata() -> Optional[Dict[str, Any]]:
    """Load metadata from JSON file."""
    try:
        if not metadata_file or not metadata_file.exists():
            logger.warning("Metadata file not found")
            return None

        with open(metadata_file, "r") as f:
            return json.load(f)

    except Exception as e:
        logger.error(f"Failed to load metadata: {e}")
        return None


@mcp.tool()
async def create_portal_account(
    site: str,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
) -> dict:
    """
    Create account on job portal.

    Args:
        site: Portal name (LinkedIn, Indeed, etc.)
        email: Account email
        password: Account password
        first_name: User first name
        last_name: User last name

    Returns:
        Dictionary with account creation result
    """
    if not page or not form_filler:
        return {
            "status": "error",
            "error": "Browser not initialized",
        }

    try:
        portal_metadata = {
            "site": site,
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "signup_url": f"https://{site.lower()}.com/signup",
        }

        return await create_account(page, portal_metadata, form_filler)

    except Exception as e:
        logger.error(f"Account creation error: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


@mcp.tool()
async def submit_application(
    position: str,
    company: str,
    application_url: str,
    use_metadata: bool = True,
) -> dict:
    """
    Submit job application.

    Args:
        position: Job position title
        company: Company name
        application_url: URL of application form
        use_metadata: Use personal info from metadata file

    Returns:
        Dictionary with submission result
    """
    if not page or not form_filler:
        return {
            "status": "error",
            "error": "Browser not initialized",
        }

    try:
        # Get personal info from metadata
        metadata = await get_metadata()
        if not metadata:
            return {
                "status": "error",
                "error": "Metadata file not found",
            }

        personal_info = metadata.get("personal_info", {})
        job_metadata = {
            "position": position,
            "company": company,
            "application_url": application_url,
            "resume_field_selector": "input[name='resume']",
        }

        return await fill_application(page, job_metadata, personal_info, form_filler)

    except Exception as e:
        logger.error(f"Application submission error: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


@mcp.tool()
async def process_redirect(max_redirects: int = 5) -> dict:
    """
    Handle OAuth redirects during application process.

    Args:
        max_redirects: Maximum redirects to follow

    Returns:
        Dictionary with redirect handling result
    """
    if not page:
        return {
            "status": "error",
            "error": "Browser not initialized",
        }

    try:
        return await handle_redirect(page, {"max_redirects": max_redirects})

    except Exception as e:
        logger.error(f"Redirect handling error: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


async def initialize_browser() -> bool:
    """Initialize Playwright browser."""
    global page, form_filler

    try:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)

        page = await browser.new_page(
            viewport={"width": 1920, "height": 1080},
        )

        form_filler = FormFiller()
        logger.info("Browser initialized for job portal automation")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize browser: {e}")
        return False


def load_metadata_path() -> None:
    """Load metadata file path from environment."""
    global metadata_file

    path = os.getenv("METADATA_FILE", "~/.llm_agent/metadata.json")
    metadata_file = Path(path).expanduser()
    logger.info(f"Metadata file path: {metadata_file}")


@mcp.on_startup
async def on_startup() -> None:
    """Initialize server on startup."""
    logger.info("Job Portal MCP Server starting...")
    load_metadata_path()
    await initialize_browser()


@mcp.on_shutdown
async def on_shutdown() -> None:
    """Cleanup on shutdown."""
    global page
    if page:
        await page.close()
        logger.info("Browser closed")


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        "logs/jobportal_mcp.log",
        rotation="10 MB",
        retention=3,
        level="DEBUG",
    )

    logger.info("Starting Job Portal MCP Server...")
    mcp.run()
