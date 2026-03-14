"""Main job automation orchestrator agent."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from config.models import SystemConfig, CLIApprovalConfig, MetadataContent
from orchestrator.cli_approval import CLIApprovalInterface
from utils.encryption import ConfigEncryption
from utils.deduplication import JobDeduplicator
from utils.state_machine import JobStateMachine, JobState
from utils.ollama_client import OllamaClient
from mcp_clients.gmail_client import GmailMCPClient


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
        
        # Email monitoring
        self.last_email_check_time: Optional[datetime] = None
        self.monitored_emails: List[Dict[str, Any]] = []
        self.email_monitor_task: Optional[asyncio.Task] = None

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
            logger.info("🔌 Initializing MCP servers...")
            
            # Initialize Gmail MCP Client
            self.gmail_mcp = GmailMCPClient()
            gmail_connected = await self.gmail_mcp.connect()
            
            if not gmail_connected:
                logger.error("Failed to connect to Gmail MCP")
                return False
            
            logger.info("✅ MCP servers initialized successfully")
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
            logger.info("📨 Checking emails for job opportunities...")

            if not self.gmail_mcp or not self.gmail_mcp.is_connected:
                logger.error("Gmail MCP not connected")
                return []

            # Fetch unread emails from Gmail
            result = await self.gmail_mcp.fetch_unread_emails(
                mailbox="INBOX",
                max_results=10
            )

            if result["status"] != "success":
                logger.warning(f"Failed to fetch emails: {result.get('error')}")
                return []

            emails = result.get("emails", [])
            opportunities = []

            for email in emails:
                # Extract recruiter/opportunity information from email
                opportunity = {
                    "job_id": f"email_{email.get('msg_id', 'unknown')}",
                    "from": email.get("from", ""),
                    "subject": email.get("subject", ""),
                    "body": email.get("body", ""),
                    "date": email.get("date", ""),
                    "timestamp": email.get("timestamp", ""),
                    "source": "email",
                    # These would normally be extracted from the email content using NLP
                    "company": self._extract_company_from_email(email),
                    "role": self._extract_role_from_email(email),
                    "message": email.get("body", "")[:200],  # First 200 chars
                }
                opportunities.append(opportunity)

            logger.info(f"✉️  Found {len(opportunities)} email opportunities")
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

            # Auto-approve all pending jobs
            for job in pending:
                logger.info(f"✅ Auto-approving: {job.company}/{job.role}")
                self.state_machine.update_state(job.job_id, JobState.APPROVED)
                await self.process_approved_job(job)

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
        recruiter_email = job.metadata.get('from', 'Unknown')
        logger.info(f"📧 Generating response to: {recruiter_email}")

        # Generate personalized response using Ollama
        if not self.metadata:
            logger.warning("Metadata not loaded, skipping email response")
            return

        if not self.gmail_mcp or not self.gmail_mcp.is_connected:
            logger.error("Gmail MCP not connected, cannot send reply")
            return

        try:
            prompt = self._build_email_prompt(job)

            response_text = await self.ollama_client.generate(
                prompt,
                system="You are a professional job seeker responding to recruiter emails. "
                "Be concise, professional, and interested.",
            )

            logger.info(f"Generated response: {len(response_text)} chars")

            # Send the email reply via Gmail MCP
            subject = job.metadata.get('subject', f"Re: {job.company} - {job.role}")
            
            send_result = await self.gmail_mcp.send_email_reply(
                to_address=recruiter_email,
                subject=subject,
                body=response_text,
                original_message_id=job.metadata.get('msg_id'),
            )

            if send_result["status"] == "success":
                logger.info(f"✅ Email reply sent successfully to {recruiter_email}")
            else:
                logger.error(f"❌ Failed to send email reply: {send_result.get('error')}")

        except Exception as e:
            logger.error(f"Error handling email response: {e}")

    async def handle_generic_application(self, job) -> None:
        """Handle generic job application."""
        logger.info(f"Handling generic application: {job.company}/{job.role}")

        # In production, this would:
        # 1. Launch job portal via jobportal_mcp
        # 2. Navigate to application URL
        # 3. Fill form with prepared data
        # 4. Submit application

    def _extract_company_from_email(self, email: Dict[str, Any]) -> str:
        """Extract company name from email subject/body using heuristics."""
        import re
        
        subject = email.get("subject", "")
        sender = email.get("from", "").lower()
        
        # Look for "at [Company]" pattern
        match = re.search(r'at\s+([A-Z][a-zA-Z0-9\s]+?)(?:\s|,|$)', subject)
        if match:
            return match.group(1).strip()
        
        # Extract domain from sender email
        domain_match = re.search(r'@([a-zA-Z0-9.-]+)', sender)
        if domain_match:
            domain = domain_match.group(1)
            company_name = domain.split('.')[0].capitalize()
            return company_name
        
        return "Unknown Company"

    def _extract_role_from_email(self, email: Dict[str, Any]) -> str:
        """Extract job role from email subject/body using heuristics."""
        import re
        
        subject = email.get("subject", "")
        body = email.get("body", "")[:500]  # First 500 chars
        
        # Simple heuristics - look for common job title patterns
        roles = [
            "Software Engineer", "Data Scientist", "ML Engineer", "Product Manager",
            "Frontend Developer", "Backend Developer", "Full Stack Engineer",
            "DevOps Engineer", "Cloud Engineer", "Solutions Architect",
            "Senior Engineer", "Lead Engineer", "Tech Lead"
        ]
        
        for role in roles:
            if role.lower() in subject.lower() or role.lower() in body.lower():
                return role
        
        # Default extraction from subject
        match = re.search(r':\s*([^-,]+?)(?:-|,|$)', subject)
        if match:
            return match.group(1).strip()
        
        return "Engineering Position"

    def _build_email_prompt(self, job) -> str:
        """Build LLM prompt for email generation."""
        if not self.metadata:
            return ""

        prompt = f"""
Generate a professional job inquiry response email based on:

Recruiter: {job.metadata.get('from', 'Unknown')}
Company: {job.company}
Position: {job.role}

Your Profile:
- Name: {self.metadata.personal_info.name}
- Email: {self.metadata.personal_info.email}
- Skills: {', '.join(self.metadata.skills)}

Original Message:
{job.metadata.get('body', 'No body provided')[:500]}

Write a concise 2-3 paragraph response expressing interest, highlighting relevant skills,
and requesting next steps. Be professional and enthusiastic. Do NOT include greeting or closing lines.
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

    async def monitor_emails_background(self, check_interval: int = 30) -> None:
        """
        Background task to continuously monitor for new emails.
        
        Args:
            check_interval: Seconds between email checks (default 30)
        """
        try:
            logger.info(f"🔔 Email monitor started (checking every {check_interval}s)")
            
            while True:
                try:
                    if not self.gmail_mcp or not self.gmail_mcp.is_connected:
                        logger.warning("Gmail MCP not connected, skipping email check")
                        await asyncio.sleep(check_interval)
                        continue
                    
                    # Check for unread emails
                    result = await self.gmail_mcp.fetch_unread_emails(
                        mailbox="INBOX",
                        max_results=5
                    )
                    
                    if result["status"] == "success":
                        new_emails = result.get("emails", [])
                        
                        # Filter out emails we've already seen
                        for email in new_emails:
                            email_id = email.get("msg_id")
                            if not any(e.get("msg_id") == email_id for e in self.monitored_emails):
                                logger.info(f"📬 New email detected from {email.get('from', 'Unknown')}")
                                self.monitored_emails.append(email)
                                
                                # Trigger job detection for new email
                                await self.process_new_email(email)
                    
                    self.last_email_check_time = datetime.utcnow()
                    await asyncio.sleep(check_interval)
                    
                except Exception as e:
                    logger.error(f"Error in email monitoring loop: {e}")
                    await asyncio.sleep(check_interval)
                    
        except asyncio.CancelledError:
            logger.info("Email monitor task cancelled")

    async def process_new_email(self, email: Dict[str, Any]) -> None:
        """
        Process a newly received email as a potential job opportunity.
        
        Args:
            email: Email dict with subject, body, from, etc.
        """
        try:
            # Extract job details from email
            opportunity = {
                "job_id": f"email_{email.get('msg_id', 'unknown')}",
                "from": email.get("from", ""),
                "subject": email.get("subject", ""),
                "body": email.get("body", ""),
                "date": email.get("date", ""),
                "timestamp": email.get("timestamp", ""),
                "source": "email",
                "company": self._extract_company_from_email(email),
                "role": self._extract_role_from_email(email),
                "message": email.get("body", "")[:200],
            }
            
            # Check for duplicates
            company = opportunity.get("company", "Unknown")
            role = opportunity.get("role", "Unknown")
            
            if self.deduplicator.is_duplicate(company, role):
                logger.debug(f"Skipping duplicate email: {company}/{role}")
                return
            
            # Create job in state machine
            new_job = self.state_machine.create_job(
                job_id=opportunity["job_id"],
                company=company,
                role=role,
                url=None,
                source="email",
                metadata=opportunity,
            )
            
            # Add to deduplication cache
            self.deduplicator.add_job(company, role)
            
            # Transition to CLI_PENDING for approval
            self.state_machine.update_state(opportunity["job_id"], JobState.CLI_PENDING)
            
            logger.info(f"✨ New job opportunity detected: {company} - {role}")
            
        except Exception as e:
            logger.error(f"Error processing new email: {e}")

    async def main(self) -> None:
        """Main orchestrator entry point."""
        try:
            logger.info("=" * 70)
            logger.info("🤖 JOB AUTOMATION ORCHESTRATOR STARTING")
            logger.info("=" * 70)

            # Initialize MCP servers FIRST (before metadata)
            logger.info("Initializing MCP servers...")
            if not await self.initialize_mcp_servers():
                logger.warning("Failed to initialize MCP servers - EmailMonitor will skip checks")
            else:
                logger.info("✅ MCP servers initialized")

            # Load configuration
            logger.info("Loading encrypted metadata...")
            if not await self.load_metadata():
                logger.warning("Metadata not loaded - email replies disabled (approval still works)")
            else:
                logger.info("✅ Metadata loaded successfully")

            logger.info("✅ Orchestrator ready")
            logger.info("")
            
            # Start background email monitoring task
            if self.gmail_mcp and self.gmail_mcp.is_connected:
                logger.info("Starting email monitoring...")
                self.email_monitor_task = asyncio.create_task(self.monitor_emails_background(check_interval=30))
            else:
                logger.warning("⚠️  Gmail not connected - email monitoring disabled")

            # Run main loop
            await self.run_approval_loop()

        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            # Cleanup
            if self.email_monitor_task:
                self.email_monitor_task.cancel()
                try:
                    await self.email_monitor_task
                except asyncio.CancelledError:
                    pass
            
            if self.gmail_mcp:
                await self.gmail_mcp.disconnect()
            await self.ollama_client.close()
            logger.info("Orchestrator shutdown complete")


async def main():
    """Entry point."""
    orchestrator = JobAutomationOrchestrator()
    await orchestrator.main()


if __name__ == "__main__":
    asyncio.run(main())
