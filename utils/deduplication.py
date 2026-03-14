"""Deduplication logic using fuzzy matching for job opportunities."""

from typing import Set, Dict, Tuple
from thefuzz import fuzz
from loguru import logger


class JobDeduplicator:
    """Manage job deduplication using fuzzy matching on company + role."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.cache: Set[str] = set()
        self.similarity_threshold = similarity_threshold

    def _combine_key(self, company: str, role: str) -> str:
        """Combine company and role into a normalized key."""
        return f"{company.lower().strip()}|{role.lower().strip()}"

    def is_duplicate(self, company: str, role: str) -> bool:
        """Check if job is duplicate using fuzzy matching."""
        current_key = self._combine_key(company, role)

        for cached_key in self.cache:
            similarity = fuzz.token_set_ratio(current_key, cached_key) / 100.0
            if similarity >= self.similarity_threshold:
                logger.debug(
                    f"Duplicate detected: {company}/{role} "
                    f"(similarity: {similarity:.2%})"
                )
                return True

        return False

    def add_job(self, company: str, role: str) -> None:
        """Add job to deduplication cache."""
        key = self._combine_key(company, role)
        self.cache.add(key)
        logger.debug(f"Added job to cache: {company}/{role}")

    def clear_cache(self) -> None:
        """Clear the deduplication cache."""
        self.cache.clear()
        logger.info("Deduplication cache cleared")

    def get_stats(self) -> Dict[str, int]:
        """Get deduplication cache statistics."""
        return {"cached_jobs": len(self.cache)}
