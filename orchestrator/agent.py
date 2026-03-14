"""Main job automation orchestrator agent."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

from config.models import SystemConfig, CLIApprovalConfig, MetadataContent
from orchestrator.cli_approval import CLIApprovalInterface
from utils.encryption import ConfigEncryption
from utils.deduplication import JobDeduplicator
from utils.state_machine import JobStateMachine, JobState
from utils.ollama_client import OllamaClient


class JobAutomationOrchestrator:
    """Main orchestrator for job automation workflow."""

    def __init__(self):
        self.config = SystemConfig()
        self.encryption = ConfigEncryption()
        self.deduplicator = JobDeduplicator(
            similarity_threshold=self.config.dedup_similarity_threshold
        )
        self.state_machine = JobStateMachine()
        self.approval_config = CLIApprovalConfig()
        self.ollama_client = OllamaClient(
            base_url=self.config.ollama_base_url,
            model=self.config.ollama_model,
            timeout=self.config.ollama_timeout,
        )

        # MCP server clients (will be initialized as needed)
        self.gmail_mcp = None
        self.linkedin_mcp = None
        self.jobportal_mcp = None

        # Metadata cache
        self.metadata: Optional[MetadataContent] = None

        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging with loguru."""
        logger.remove()

        # Ensure logs directory exists
        logs_dir = Path(self.config.log_file).parent
        logs_dir.mkdir(parents=True, exist_ok=True)

        logger.add(
            self.config.log_file,
            rotation=self.config.log_rotation,
            retention=self.config.log_retention,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level=self.config.log_level,
        )

        logger.add(
            sys.stdout,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            level="INFO",
        )

        logger.info("Logging configured")

    async def load_metadata(self) -> bool:
        """Load and decrypt metadata JSON from file."""
        try:
            metadata_path = Path(self.config.metadata_file)

            if not metadata_path.exists():
                logger.error(f"Metadata file not found: {metadata_path}")
                return False

            # Prompt for master password
            password = ConfigEncryption.prompt_master_password()

            with open(metadata_path, "r") as f:
                encrypted_data = f.read()

            decrypted_data = self.encryption.decrypt_metadata(encrypted_data, password)
            self.metadata = MetadataContent(**decrypted_data)

            logger.info(f"Metadata loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return False

    async def initialize_mcp_servers(self) -> bool:
        """Initialize connections to MCP servers."""
        try:
            # Note: In production, use mcp.ClientSession to connect
            # For now, we'll use placeholder implementations
            logger.info("MCP server initialization skipped (placeholder mode)")
            logger.info(
                "Configure MCP_SERVERS environment variable for production use"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MCP servers: {e}")
            return False

    async def run_linkedin_discovery(self) -> List[Dict[str, Any]]:
        """Discover jobs from LinkedIn using stealth automation."""
        try:
            logger.info("Starting LinkedIn job discovery...")

            # This would call the linkedin_mcp server in production
            # For now, return mock data
            jobs = [
                {
                    "job_id": "li_001",
                    "title": "Senior Software Engineer",
                    "company": "TechCorp",
                    "location": "San Francisco, CA",
                    "url": "https://linkedin.com/jobs/view/12345",
                    "salary": "$150k-$200k",
                    "posted_date": datetime.utcnow().isoformat(),
                }
            ]

            logger.info(f"Discovered {len(jobs)} jobs from LinkedIn")
            return jobs

        except Exception as e:
            logger.error(f"LinkedIn discovery error: {e}")
            return []

    async def check_emails_for_opportunities(self) -> List[Dict[str, Any]]:
        """Check emails for job opportunities and recruiter messages."""
        try:
            logger.info("Checking emails for job opportunities...")

            # This would call the gmail_mcp server in production
            # For now, return mock data
            opportunities = [
                {
                    "job_id": "email_001",
                    "from": "recruiter@company.com",
                    "company": "DataSystems",
                    "role": "ML Engineer",
                    "message": "We think you'd be great for...",
                    "received_at": datetime.utcnow().isoformat(),
                }
            ]

            logger.info(f"Found {len(opportunities)} email opportunities")
            return opportunities

        except Exception as e:
            logger.error(f"Email check error: {e}")
            return []

    async def detect_new_jobs(self) -> None:
        """Detect new job opportunities from various sources."""
        try:
            logger.info("Running job discovery cycle...")

            # Check multiple sources
            linkedin_jobs = await self.run_linkedin_discovery()
            email_opportunities = await self.check_emails_for_opportunities()

            all_jobs = linkedin_jobs + email_opportunities

            for job in all_jobs:
                company = job.get("company", "Unknown")
                role = job.get("title") or job.get("role", "Unknown")
                job_id = job.get("job_id", f"job_{datetime.utcnow().timestamp()}")

                # Check for duplicates
                if self.deduplicator.is_duplicate(company, role):
                    logger.debug(f"Skipping duplicate: {company}/{role}")
                    continue

                # Create job in state machine
                new_job = self.state_machine.create_job(
                    job_id=job_id,
                    company=company,
                    role=role,
                    url=job.get("url"),
                    source=job.get("source", "unknown"),
                    metadata=job,
                )

                # Add to deduplication cache
                self.deduplicator.add_job(company, role)

                # Transition to CLI_PENDING for approval
                self.state_machine.update_state(job_id, JobState.CLI_PENDING)

        except Exception as e:
            logger.error(f"Job detection error: {e}")

    async def process_cli_approvals(self) -> None:
        """Process pending CLI approvals."""
        try:
            pending = self.state_machine.get_pending_approvals()

            if not pending:
                logger.info("No pending approvals")
                return

            logger.info(f"Processing {len(pending)} pending approvals...")

            # Batch action prompt
            batch_action = CLIApprovalInterface.prompt_batch_action(len(pending))

            if batch_action == "approve_all":
                for job in pending:
                    self.state_machine.update_state(job.job_id, JobState.APPROVED)
                    await self.process_approved_job(job)

            elif batch_action == "reject_all":
                for job in pending:
                    self.state_machine.update_state(job.job_id, JobState.FAILED)

            elif batch_action == "manual":
                for job in pending:
                    approved = CLIApprovalInterface.prompt_approval(
                        job.job_id,
                        job.company,
                        job.role,
                        job.url,
                        job.metadata,
                    )

                    if approved:
                        self.state_machine.update_state(job.job_id, JobState.APPROVED)
                        await self.process_approved_job(job)
                    else:
                        self.state_machine.update_state(job.job_id, JobState.FAILED)

        except Exception as e:
            logger.error(f"Approval processing error: {e}")

    async def process_approved_job(self, job) -> None:
        """Process an approved job (application or email reply)."""
        try:
            logger.info(f"Processing approved job: {job.company}/{job.role}")

            self.state_machine.update_state(job.job_id, JobState.PROCESSING)

            # Determine action based on source
            source = job.source

            if source == "linkedin":
                await self.handle_linkedin_job(job)
            elif source == "email":
                await self.handle_email_response(job)
            else:
                await self.handle_generic_application(job)

            self.state_machine.update_state(job.job_id, JobState.COMPLETED)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Job processing error: {error_msg}")
            self.state_machine.update_state(job.job_id, JobState.FAILED, error_msg)

    async def handle_linkedin_job(self, job) -> None:
        """Handle LinkedIn job application."""
        logger.info(f"Handling LinkedIn job: {job.company}/{job.role}")

        # In production, this would:
        # 1. Navigate to job URL
        # 2. Click "Apply" button
        # 3. Fill application form with metadata
        # 4. Submit application

        logger.info(f"Applied to: {job.company}/{job.role}")

    async def handle_email_response(self, job) -> None:
        """Handle recruiter email response."""
        logger.info(f"Generating response to: {job.metadata.get('from')}")

        # Generate personalized response using Ollama
        if not self.metadata:
            logger.warning("Metadata not loaded, skipping email response")
            return

        prompt = self._build_email_prompt(job)

        response_text = await self.ollama_client.generate(
            prompt,
            system="You are a professional job seeker responding to recruiter emails. "
            "Be concise, professional, and interested.",
        )

        logger.info(f"Generated response length: {len(response_text)} chars")

        # In production, this would:
        # 1. Call gmail_mcp to send email reply
        # 2. Update job application status

    async def handle_generic_application(self, job) -> None:
        """Handle generic job application."""
        logger.info(f"Handling generic application: {job.company}/{job.role}")

        # In production, this would:
        # 1. Launch job portal via jobportal_mcp
        # 2. Navigate to application URL
        # 3. Fill form with prepared data
        # 4. Submit application

    def _build_email_prompt(self, job) -> str:
        """Build LLM prompt for email generation."""
        if not self.metadata:
            return ""

        thread_context = job.metadata.get("thread", [])

        prompt = f"""
        Generate a professional job inquiry response email based on:

        Recruiter: {job.metadata.get('from', 'Unknown')}
        Company: {job.company}
        Position: {job.role}

        Your Profile:
        - Name: {self.metadata.personal_info.name}
        - Email: {self.metadata.personal_info.email}
        - Skills: {', '.join(self.metadata.skills)}

        Previous Message:
        {json.dumps(thread_context, indent=2)}

        Write a 2-3 paragraph response expressing interest, highlighting relevant skills,
        and requesting next steps. Keep it professional and concise.
        """

        return prompt

    async def run_approval_loop(self) -> None:
        """Run the main approval loop."""
        try:
            while True:
                logger.info("------- Approval Loop Cycle -------")

                # Check for new jobs
                await self.detect_new_jobs()

                # Process approvals
                await self.process_cli_approvals()

                # Print current state
                stats = self.state_machine.get_stats()
                logger.info(f"Job Statistics: {stats}")

                # Wait before next cycle
                logger.info("Waiting 60 seconds before next cycle...")
                await asyncio.sleep(60)

        except KeyboardInterrupt:
            logger.info("Approval loop interrupted by user")
        except Exception as e:
            logger.error(f"Approval loop error: {e}")

    async def main(self) -> None:
        """Main orchestrator entry point."""
        try:
            logger.info("=" * 70)
            logger.info("🤖 JOB AUTOMATION ORCHESTRATOR STARTING")
            logger.info("=" * 70)

            # Load configuration
            logger.info("Loading encrypted metadata...")
            if not await self.load_metadata():
                logger.error("Failed to load metadata, exiting")
                return

            # Initialize MCP servers
            logger.info("Initializing MCP servers...")
            if not await self.initialize_mcp_servers():
                logger.error("Failed to initialize MCP servers")
                # Continue anyway in development mode

            logger.info("✅ Orchestrator ready")
            logger.info("")

            # Run main loop
            await self.run_approval_loop()

        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            # Cleanup
            await self.ollama_client.close()
            logger.info("Orchestrator shutdown complete")


async def main():
    """Entry point."""
    orchestrator = JobAutomationOrchestrator()
    await orchestrator.main()


if __name__ == "__main__":
    asyncio.run(main())
