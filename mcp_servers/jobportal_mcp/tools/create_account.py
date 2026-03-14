"""Tool for creating accounts on job portals."""

from typing import Dict, Optional
from loguru import logger


async def create_account(
    browser,
    portal_metadata: Dict,
    form_filler,
) -> Dict:
    """
    Create account on job portal.

    Args:
        browser: Playwright page instance
        portal_metadata: Portal login details from metadata JSON
        form_filler: FormFiller instance

    Returns:
        Dictionary with creation result
    """
    try:
        max_retries = 3
        for attempt in range(max_retries):
            logger.info(
                f"Account creation attempt {attempt + 1}/{max_retries} "
                f"for {portal_metadata.get('site')}"
            )

            # Navigate to signup page
            signup_url = portal_metadata.get("signup_url")
            if not signup_url:
                return {
                    "status": "error",
                    "error": "signup_url not provided in metadata",
                }

            await browser.goto(signup_url, wait_until="networkidle")

            # Fill signup form
            form_data = {
                "input[name='email']": portal_metadata.get("email", ""),
                "input[name='password']": portal_metadata.get("password", ""),
                "input[name='firstName']": portal_metadata.get("first_name", ""),
                "input[name='lastName']": portal_metadata.get("last_name", ""),
            }

            success = await form_filler.fill_form(browser, form_data)
            if not success:
                logger.warning(f"Failed to fill form on attempt {attempt + 1}")
                continue

            # Submit form
            await browser.click("button[type='submit']")
            await browser.wait_for_load_state("networkidle")

            # Check for success
            if await browser.query_selector("[data-success]"):
                logger.info(f"Account created successfully for {portal_metadata.get('site')}")
                return {
                    "status": "success",
                    "site": portal_metadata.get("site"),
                    "email": portal_metadata.get("email"),
                }

            logger.warning(f"Account creation failed on attempt {attempt + 1}")

        return {
            "status": "failed",
            "error": "Max retries exceeded",
            "site": portal_metadata.get("site"),
        }

    except Exception as e:
        logger.error(f"Account creation error: {e}")
        return {
            "status": "error",
            "error": str(e),
        }
