"""Tool for handling redirects during job applications."""

from typing import Dict, Optional
from loguru import logger


async def handle_redirect(
    browser,
    redirect_handler_config: Dict,
) -> Dict:
    """
    Handle redirects during job application process.

    Args:
        browser: Playwright page instance
        redirect_handler_config: Configuration for handling redirects

    Returns:
        Dictionary with redirect handling result
    """
    try:
        max_redirects = redirect_handler_config.get("max_redirects", 5)
        redirect_count = 0

        while redirect_count < max_redirects:
            current_url = browser.url

            # Check for known redirect patterns
            if "linkedin.com/oauth" in current_url:
                logger.info("LinkedIn OAuth redirect detected")
                # Wait for OAuth completion
                await browser.wait_for_url("**/")
                redirect_count += 1

            elif "google.com/accounts" in current_url:
                logger.info("Google OAuth redirect detected")
                # Wait for Google auth completion
                await browser.wait_for_url("**/")
                redirect_count += 1

            else:
                # No more redirects
                break

        logger.info(f"Handled {redirect_count} redirects")
        return {
            "status": "success",
            "redirects_handled": redirect_count,
            "final_url": browser.url if hasattr(browser, 'url') else None,
        }

    except Exception as e:
        logger.error(f"Redirect handling error: {e}")
        return {
            "status": "error",
            "error": str(e),
        }
