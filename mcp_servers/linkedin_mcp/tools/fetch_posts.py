"""Tool for fetching job postings from LinkedIn."""

from typing import Dict, Optional
from loguru import logger
from dotenv import load_dotenv
load_dotenv()


async def fetch_job_posts(
    browser,
    search_query: str = "Job postings",
    max_results: int = 10,
    filters: Optional[Dict] = None,
) -> Dict:
    """
    Fetch recent job posts from LinkedIn.

    Args:
        browser: StealthBrowser instance
        search_query: Search query for job postings
        max_results: Maximum posts to retrieve (top 10)
        filters: Optional filters (experience, location, etc.)

    Returns:
        Dictionary with job post data
    """
    try:
        await browser.goto_with_delay("https://www.linkedin.com/jobs/search/")

        # Wait for job search page to load
        if not await browser.wait_for_selector("[data-job-id]"):
            logger.warning("Job posts not found on page")
            return {
                "status": "no_jobs",
                "posts": [],
                "count": 0,
            }

        # Extract job posts from page
        jobs = await browser.page.evaluate(
            f"""
            () => {{
                const posts = document.querySelectorAll('[data-job-id]');
                return Array.from(posts.slice(0, {max_results})).map(post => ({{
                    id: post.getAttribute('data-job-id'),
                    title: post.querySelector('h3')?.textContent || '',
                    company: post.querySelector('[data-job-search-card-company]')?.textContent || '',
                    location: post.querySelector('[data-job-search-card-location]')?.textContent || '',
                    url: post.querySelector('a')?.href || '',
                    timestamp: new Date().toISOString(),
                }}));
            }}
            """
        )

        logger.info(f"Fetched {len(jobs)} job posts from LinkedIn")
        return {
            "status": "success",
            "posts": jobs,
            "count": len(jobs),
        }

    except Exception as e:
        logger.error(f"Failed to fetch job posts: {e}")
        return {
            "status": "error",
            "error": str(e),
            "posts": [],
            "count": 0,
        }
