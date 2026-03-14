"""CLI interface for human-in-the-loop approval workflow."""

from typing import Optional, Dict
from loguru import logger
from dotenv import load_dotenv
load_dotenv()

class CLIApprovalInterface:
    """Handle CLI-based approval for job applications."""

    @staticmethod
    def prompt_approval(
        job_id: str,
        company: str,
        role: str,
        job_url: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Prompt user for approval via CLI.

        Args:
            job_id: Job unique identifier
            company: Company name
            role: Job role/position
            job_url: URL to job posting
            metadata: Additional metadata about job

        Returns:
            True if approved, False if rejected
        """
        print("\n" + "=" * 60)
        print("🤖 JOB APPROVAL REQUEST")
        print("=" * 60)
        print(f"Job ID:   {job_id}")
        print(f"Company:  {company}")
        print(f"Role:     {role}")

        if job_url:
            print(f"URL:      {job_url}")

        if metadata:
            for key, value in metadata.items():
                if key not in ["url", "id"]:
                    print(f"  {key}: {value}")

        print("\n" + "-" * 60)
        print("Options:")
        print("  [y] Approve and process this application")
        print("  [n] Reject and skip this application")
        print("  [v] View full details")
        print("-" * 60)

        while True:
            user_input = input("\nYour choice [y/n/v]: ").lower().strip()

            if user_input == "y":
                logger.info(f"User APPROVED job {job_id}: {company}/{role}")
                return True

            elif user_input == "n":
                logger.info(f"User REJECTED job {job_id}: {company}/{role}")
                return False

            elif user_input == "v":
                CLIApprovalInterface._print_details(job_id, metadata)
                continue

            else:
                print("Invalid input. Please enter 'y', 'n', or 'v'.")

    @staticmethod
    def _print_details(job_id: str, metadata: Optional[Dict]) -> None:
        """Print detailed job information."""
        print("\nFull Details:")
        print("-" * 60)
        if metadata:
            import json
            print(json.dumps(metadata, indent=2))
        print("-" * 60)

    @staticmethod
    def prompt_batch_action(
        pending_count: int,
    ) -> Optional[str]:
        """
        Prompt for batch action on pending approvals.

        Args:
            pending_count: Number of pending approvals

        Returns:
            'approve_all', 'reject_all', 'manual', or None
        """
        if pending_count == 0:
            return None

        print(f"\n📋 You have {pending_count} pending job approval(s)")
        print("Options:")
        print("  [a] Approve all")
        print("  [r] Reject all")
        print("  [m] Manual review each")
        print("  [q] Quit")

        while True:
            choice = input("\nYour choice [a/r/m/q]: ").lower().strip()

            if choice in ["a", "r", "m", "q"]:
                return {"a": "approve_all", "r": "reject_all", "m": "manual", "q": None}.get(
                    choice
                )
            else:
                print("Invalid choice. Please enter 'a', 'r', 'm', or 'q'.")

    @staticmethod
    def print_status(job_id: str, status: str, message: Optional[str] = None) -> None:
        """
        Print job status update.

        Args:
            job_id: Job identifier
            status: Status message
            message: Optional additional message
        """
        emoji_map = {
            "DETECTED": "🔍",
            "CLI_PENDING": "⏳",
            "APPROVED": "✅",
            "PROCESSING": "⚙️",
            "COMPLETED": "🎉",
            "FAILED": "❌",
        }

        emoji = emoji_map.get(status, "📌")
        print(f"{emoji} {job_id}: {status}")

        if message:
            print(f"   → {message}")
