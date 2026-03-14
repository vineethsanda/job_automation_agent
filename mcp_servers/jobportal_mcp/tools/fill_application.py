"""Tool for filling job application forms."""

from typing import Dict, Optional
from loguru import logger


async def fill_application(
    browser,
    job_metadata: Dict,
    personal_info: Dict,
    form_filler,
) -> Dict:
    """
    Fill and submit job application form.

    Args:
        browser: Playwright page instance
        job_metadata: Job posting metadata
        personal_info: Applicant personal information
        form_filler: FormFiller instance

    Returns:
        Dictionary with submission result
    """
    try:
        # Navigate to application URL
        app_url = job_metadata.get("application_url")
        if not app_url:
            return {
                "status": "error",
                "error": "application_url not provided",
            }

        await browser.goto(app_url, wait_until="networkidle")

        # Prepare form data
        form_data = {
            "input[name='firstName']": personal_info.get("first_name", ""),
            "input[name='lastName']": personal_info.get("last_name", ""),
            "input[name='email']": personal_info.get("email", ""),
            "input[name='phone']": personal_info.get("phone", ""),
        }

        # Fill form fields
        success = await form_filler.fill_form(browser, form_data)
        if not success:
            logger.error("Failed to fill application form")
            return {
                "status": "error",
                "error": "Form filling failed",
            }

        # Upload resume if selector provided
        resume_selector = job_metadata.get("resume_field_selector")
        resume_path = personal_info.get("resume_path")

        if resume_selector and resume_path:
            upload_success = await form_filler.upload_file(
                browser, resume_selector, resume_path
            )
            if not upload_success:
                logger.warning("Failed to upload resume")

        # Submit application
        await browser.click("button[type='submit']")
        await browser.wait_for_load_state("networkidle")

        logger.info(f"Application submitted for {job_metadata.get('position')}")
        return {
            "status": "success",
            "job_id": job_metadata.get("job_id"),
            "position": job_metadata.get("position"),
            "company": job_metadata.get("company"),
        }

    except Exception as e:
        logger.error(f"Application submission error: {e}")
        return {
            "status": "error",
            "error": str(e),
        }
