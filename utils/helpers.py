"""Utility and helper functions for the job automation agent."""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class AgentUtils:
    """Utility functions for agent operations."""

    @staticmethod
    def print_banner() -> None:
        """Print agent banner."""
        banner = """
        ╔══════════════════════════════════════════════════════════╗
        ║      🤖 JOB AUTOMATION AGENT                             ║
        ║      Local Llama 3.1 8B via Ollama                       ║
        ║      Mac mini M4                                         ║
        ╚══════════════════════════════════════════════════════════╝
        """
        print(banner)

    @staticmethod
    def load_json_file(path: str) -> Optional[Dict[str, Any]]:
        """Safely load JSON file."""
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
            return None

    @staticmethod
    def save_json_file(path: str, data: Dict[str, Any]) -> bool:
        """Safely save JSON file."""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save {path}: {e}")
            return False

    @staticmethod
    async def retry_async(
        coro,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
    ):
        """Retry async operation with exponential backoff."""
        attempt = 0
        current_delay = delay

        while attempt < max_attempts:
            try:
                return await coro
            except Exception as e:
                attempt += 1
                if attempt >= max_attempts:
                    raise

                logger.warning(
                    f"Attempt {attempt} failed, retrying in {current_delay}s: {e}"
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        invalid_chars = r'<>:"/\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        return filename

    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Truncate text with ellipsis."""
        if len(text) > max_length:
            return text[: max_length - 3] + "..."
        return text

    @staticmethod
    def format_job_summary(job) -> str:
        """Format job information for display."""
        return f"{job.company} - {job.role} [{job.state.value}]"


class PerformanceMonitor:
    """Monitor agent performance metrics."""

    def __init__(self):
        self.metrics = {
            "jobs_detected": 0,
            "jobs_approved": 0,
            "jobs_completed": 0,
            "jobs_failed": 0,
            "duplicates_skipped": 0,
            "emails_sent": 0,
            "applications_submitted": 0,
        }

    def record_event(self, event: str) -> None:
        """Record a metric event."""
        if event in self.metrics:
            self.metrics[event] += 1
            logger.debug(f"Metric recorded: {event} (total: {self.metrics[event]})")

    def get_stats(self) -> Dict[str, int]:
        """Get all metrics."""
        return self.metrics.copy()

    def print_report(self) -> None:
        """Print performance report."""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE METRICS")
        print("=" * 60)

        for metric, value in self.metrics.items():
            print(f"  {metric}: {value}")

        total_jobs = (
            self.metrics["jobs_completed"] + self.metrics["jobs_failed"]
        )
        if total_jobs > 0:
            success_rate = (
                self.metrics["jobs_completed"] / total_jobs * 100
            )
            print(f"\n  Success rate: {success_rate:.1f}%")

        print("=" * 60)


class HealthCheck:
    """Health check for agent components."""

    def __init__(self, ollama_client, config):
        self.ollama = ollama_client
        self.config = config

    async def check_ollama(self) -> bool:
        """Check Ollama connectivity."""
        try:
            # Try a simple generation
            result = await self.ollama.generate(
                "Hi",
                timeout=5,
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def check_gmail(self) -> bool:
        """Check Gmail connectivity."""
        return bool(self.config.gmail_address and self.config.gmail_app_password)

    async def run_all_checks(self) -> Dict[str, bool]:
        """Run all health checks."""
        checks = {
            "ollama": await self.check_ollama(),
            "gmail": await self.check_gmail(),
        }

        logger.info(f"Health check results: {checks}")
        return checks

    async def print_health_report(self) -> None:
        """Print health check report."""
        checks = await self.run_all_checks()

        print("\n" + "=" * 60)
        print("🏥 HEALTH CHECK")
        print("=" * 60)

        for service, status in checks.items():
            emoji = "✅" if status else "❌"
            print(f"  {emoji} {service.upper()}")

        all_ok = all(checks.values())
        status = "Ready to start" if all_ok else "Issues detected"
        print(f"\nStatus: {status}")
        print("=" * 60)
