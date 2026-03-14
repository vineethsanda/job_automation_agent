"""Form filling utilities for job portal automation."""

from typing import Dict, Optional
from loguru import logger


class FormFiller:
    """Handle form filling on job portal websites."""

    @staticmethod
    async def fill_text_field(
        page,
        selector: str,
        value: str,
        clear_first: bool = True,
    ) -> bool:
        """Fill text input field."""
        try:
            if clear_first:
                await page.fill(selector, "")

            await page.type(selector, value, delay=50)
            logger.debug(f"Filled {selector} with text")
            return True

        except Exception as e:
            logger.error(f"Failed to fill {selector}: {e}")
            return False

    @staticmethod
    async def select_dropdown(
        page,
        selector: str,
        value: str,
    ) -> bool:
        """Select option from dropdown."""
        try:
            await page.select_option(selector, value)
            logger.debug(f"Selected {value} from dropdown {selector}")
            return True

        except Exception as e:
            logger.error(f"Failed to select dropdown {selector}: {e}")
            return False

    @staticmethod
    async def fill_form(
        page,
        form_data: Dict[str, str],
    ) -> bool:
        """Fill multiple form fields."""
        for selector, value in form_data.items():
            if not await FormFiller.fill_text_field(page, selector, value):
                return False

        return True

    @staticmethod
    async def upload_file(
        page,
        file_input_selector: str,
        file_path: str,
    ) -> bool:
        """Upload file to form."""
        try:
            await page.set_input_files(file_input_selector, file_path)
            logger.debug(f"Uploaded file to {file_input_selector}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return False

    @staticmethod
    async def check_checkbox(
        page,
        selector: str,
        checked: bool = True,
    ) -> bool:
        """Check or uncheck checkbox."""
        try:
            if checked:
                await page.check(selector)
            else:
                await page.uncheck(selector)

            logger.debug(f"Set checkbox {selector} to {checked}")
            return True

        except Exception as e:
            logger.error(f"Failed to set checkbox: {e}")
            return False
