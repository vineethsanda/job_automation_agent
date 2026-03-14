"""Tool for managing LinkedIn session state."""

from typing import Dict
from loguru import logger


async def manage_session(
    cookie_store,
    action: str = "status",
) -> Dict:
    """
    Manage LinkedIn session state.

    Args:
        cookie_store: CookieStore instance
        action: 'status', 'save', 'load', or 'clear'

    Returns:
        Dictionary with session information
    """
    try:
        if action == "status":
            status = cookie_store.get_session_status()
            return {
                "status": "success",
                "action": "status",
                "session": status,
            }

        elif action == "save":
            # Cookies are saved by browser.save_cookies()
            return {
                "status": "success",
                "action": "save",
            }

        elif action == "load":
            cookies = cookie_store.load_cookies()
            return {
                "status": "success" if cookies else "no_session",
                "action": "load",
                "cookie_count": len(cookies) if cookies else 0,
            }

        elif action == "clear":
            cookie_store.clear_cookies()
            return {
                "status": "success",
                "action": "clear",
            }

        else:
            return {
                "status": "error",
                "error": f"Unknown action: {action}",
            }

    except Exception as e:
        logger.error(f"Session management error: {e}")
        return {
            "status": "error",
            "error": str(e),
        }
