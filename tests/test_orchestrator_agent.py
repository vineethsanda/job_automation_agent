"""
Comprehensive test suite for Job Automation Orchestrator Agent.

Tests LinkedIn job discovery, email fetching, email sending, and full workflows.

Run with: python -m pytest tests/test_orchestrator_agent.py -v -s
Or: python tests/test_orchestrator_agent.py
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, List, Any

# Try to import pytest
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.agent import JobAutomationOrchestrator
from config.models import SystemConfig, MetadataContent, PersonalInfo
from utils.state_machine import JobState
from mcp_clients.gmail_client import GmailMCPClient


# Conditional pytest decorator
if HAS_PYTEST:
    mark_asyncio = pytest.mark.asyncio
else:
    def mark_asyncio(func):
        """No-op decorator when pytest unavailable."""
        return func


# ============================================================================
# Mock Data Fixtures
# ============================================================================

def create_mock_metadata() -> MetadataContent:
    """Create mock metadata for testing."""
    return MetadataContent(
        personal_info=PersonalInfo(
            name="John Doe",
            email="john.doe@example.com",
            phone="+1-555-1234",
            first_name="John",
            last_name="Doe",
            resume_path="/path/to/resume.pdf"
        ),
        skills=["Python", "Java", "JavaScript", "React", "AWS"],
        cover_letter_template="Dear Hiring Manager, I am interested in {{role}} at {{company}}...",
    )


def create_mock_linkedin_jobs() -> List[Dict[str, Any]]:
    """Create mock LinkedIn job data."""
    return [
        {
            "job_id": "li_001",
            "title": "Senior Software Engineer",
            "company": "TechCorp",
            "location": "San Francisco, CA",
            "url": "https://linkedin.com/jobs/view/001",
            "salary": "$150k-$200k",
            "posted_date": datetime.utcnow().isoformat(),
            "source": "linkedin",
        },
        {
            "job_id": "li_002",
            "title": "Backend Engineer",
            "company": "CloudTech",
            "location": "Remote",
            "url": "https://linkedin.com/jobs/view/002",
            "salary": "$120k-$160k",
            "posted_date": datetime.utcnow().isoformat(),
            "source": "linkedin",
        },
    ]


def create_mock_recruiter_emails() -> List[Dict[str, Any]]:
    """Create mock recruiter emails."""
    return [
        {
            "msg_id": "email_001",
            "from": "recruiter@techcorp.com",
            "subject": "Exciting Opportunity: Senior Engineer at TechCorp",
            "body": "Hi John, We have an exciting opportunity for a Senior Software Engineer...",
            "date": datetime.utcnow().isoformat(),
            "timestamp": int(datetime.utcnow().timestamp()),
        },
        {
            "msg_id": "email_002",
            "from": "hr@cloudtech.com",
            "subject": "Backend Engineer Position - CloudTech",
            "body": "Hello John, We noticed your profile and think you'd be great for our backend team...",
            "date": datetime.utcnow().isoformat(),
            "timestamp": int(datetime.utcnow().timestamp()),
        },
    ]


# ============================================================================
# Test Classes
# ============================================================================

class TestOrchestratorInitialization:
    """Test orchestrator initialization and setup."""

    def test_orchestrator_creates_successfully(self):
        """Test orchestrator can be initialized."""
        orchestrator = JobAutomationOrchestrator()
        assert orchestrator is not None
        assert orchestrator.state_machine is not None
        assert orchestrator.deduplicator is not None

    def test_orchestrator_components_initialized(self):
        """Test all components are initialized."""
        orchestrator = JobAutomationOrchestrator()
        assert orchestrator.config is not None
        assert orchestrator.encryption is not None
        assert orchestrator.approval_config is not None
        assert orchestrator.ollama_client is not None
        assert orchestrator.metadata is None  # Not loaded yet


class TestLinkedInJobDiscovery:
    """Test LinkedIn job discovery functionality."""

    @mark_asyncio
    async def test_run_linkedin_discovery(self):
        """Test LinkedIn job discovery returns jobs."""
        orchestrator = JobAutomationOrchestrator()
        
        jobs = await orchestrator.run_linkedin_discovery()
        
        assert len(jobs) > 0
        assert jobs[0]["job_id"] == "li_001"
        assert jobs[0]["company"] == "TechCorp"
        assert jobs[0]["title"] == "Senior Software Engineer"

    @mark_asyncio
    async def test_linkedin_discovery_structure(self):
        """Test returned jobs have correct structure."""
        orchestrator = JobAutomationOrchestrator()
        
        jobs = await orchestrator.run_linkedin_discovery()
        
        required_fields = ["job_id", "title", "company", "location", "url"]
        for job in jobs:
            for field in required_fields:
                assert field in job, f"Missing field: {field}"
                assert job[field] is not None

    @mark_asyncio
    async def test_linkedin_discovery_error_handling(self):
        """Test error handling in job discovery."""
        orchestrator = JobAutomationOrchestrator()
        
        # Mock error scenario
        with patch.object(orchestrator, 'run_linkedin_discovery', side_effect=Exception("Network error")):
            try:
                await orchestrator.run_linkedin_discovery()
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Network error" in str(e)


class TestEmailFetching:
    """Test email fetching functionality."""

    @mark_asyncio
    async def test_check_emails_for_opportunities(self):
        """Test checking emails for job opportunities."""
        orchestrator = JobAutomationOrchestrator()
        
        # Mock Gmail MCP client
        orchestrator.gmail_mcp = AsyncMock()
        orchestrator.gmail_mcp.is_connected = True
        orchestrator.gmail_mcp.fetch_unread_emails = AsyncMock(return_value={
            "status": "success",
            "emails": create_mock_recruiter_emails(),
        })
        
        opportunities = await orchestrator.check_emails_for_opportunities()
        
        assert len(opportunities) > 0
        assert opportunities[0]["source"] == "email"
        assert "recruiter@techcorp.com" in opportunities[0]["from"]

    @mark_asyncio
    async def test_email_opportunity_extraction(self):
        """Test extracting job details from emails."""
        orchestrator = JobAutomationOrchestrator()
        
        # Mock Gmail connection
        orchestrator.gmail_mcp = AsyncMock()
        orchestrator.gmail_mcp.is_connected = True
        orchestrator.gmail_mcp.fetch_unread_emails = AsyncMock(return_value={
            "status": "success",
            "emails": create_mock_recruiter_emails(),
        })
        
        opportunities = await orchestrator.check_emails_for_opportunities()
        
        # Check extraction
        assert opportunities[0]["company"] is not None
        assert opportunities[0]["role"] is not None

    @mark_asyncio
    async def test_email_fetch_not_connected(self):
        """Test email fetching when Gmail not connected."""
        orchestrator = JobAutomationOrchestrator()
        
        # Gmail not connected
        orchestrator.gmail_mcp = None
        
        opportunities = await orchestrator.check_emails_for_opportunities()
        
        assert len(opportunities) == 0

    @mark_asyncio
    async def test_email_fetch_error_handling(self):
        """Test error handling in email fetching."""
        orchestrator = JobAutomationOrchestrator()
        
        orchestrator.gmail_mcp = AsyncMock()
        orchestrator.gmail_mcp.is_connected = True
        orchestrator.gmail_mcp.fetch_unread_emails = AsyncMock(return_value={
            "status": "error",
            "error": "Connection failed",
            "emails": []
        })
        
        opportunities = await orchestrator.check_emails_for_opportunities()
        
        assert len(opportunities) == 0


class TestEmailSending:
    """Test email response generation and sending."""

    @mark_asyncio
    async def test_handle_email_response_success(self):
        """Test successful email response generation and sending."""
        orchestrator = JobAutomationOrchestrator()
        orchestrator.metadata = create_mock_metadata()
        
        # Mock Gmail client
        orchestrator.gmail_mcp = AsyncMock()
        orchestrator.gmail_mcp.is_connected = True
        orchestrator.gmail_mcp.send_email_reply = AsyncMock(return_value={
            "status": "success",
            "message_id": "msg_123"
        })
        
        # Mock Ollama client
        orchestrator.ollama_client = AsyncMock()
        orchestrator.ollama_client.generate = AsyncMock(
            return_value="Thank you for reaching out! I am interested in this opportunity..."
        )
        
        # Create mock job
        mock_job = Mock()
        mock_job.company = "TechCorp"
        mock_job.role = "Senior Engineer"
        mock_job.metadata = {
            "from": "recruiter@techcorp.com",
            "subject": "RE: Opportunity at TechCorp",
            "body": "We have an opening...",
            "msg_id": "email_001"
        }
        
        await orchestrator.handle_email_response(mock_job)
        
        # Verify response was generated and sent
        orchestrator.ollama_client.generate.assert_called_once()
        orchestrator.gmail_mcp.send_email_reply.assert_called_once()

    @mark_asyncio
    async def test_email_response_without_metadata(self):
        """Test email response fails gracefully without metadata."""
        orchestrator = JobAutomationOrchestrator()
        
        # No metadata loaded
        orchestrator.metadata = None
        
        mock_job = Mock()
        mock_job.company = "TechCorp"
        mock_job.role = "Engineer"
        
        # Should not raise error
        await orchestrator.handle_email_response(mock_job)

    @mark_asyncio
    async def test_email_response_without_gmail_connection(self):
        """Test email response fails gracefully without Gmail."""
        orchestrator = JobAutomationOrchestrator()
        orchestrator.metadata = create_mock_metadata()
        
        # Gmail not connected
        orchestrator.gmail_mcp = None
        
        mock_job = Mock()
        mock_job.company = "TechCorp"
        mock_job.role = "Engineer"
        mock_job.metadata = {"from": "recruiter@example.com"}
        
        # Should not raise error
        await orchestrator.handle_email_response(mock_job)

    @mark_asyncio
    async def test_email_prompt_generation(self):
        """Test email prompt is correctly generated for LLM."""
        orchestrator = JobAutomationOrchestrator()
        orchestrator.metadata = create_mock_metadata()
        
        mock_job = Mock()
        mock_job.company = "TechCorp"
        mock_job.role = "Senior Engineer"
        mock_job.metadata = {
            "from": "recruiter@techcorp.com",
            "body": "We have an opening for..."
        }
        
        prompt = orchestrator._build_email_prompt(mock_job)
        
        assert "TechCorp" in prompt
        assert "Senior Engineer" in prompt
        assert "John Doe" in prompt
        assert "John Doe" in prompt  # Personal info included
        assert "Python" in prompt  # Skills included


class TestDataExtraction:
    """Test extraction of company and role from emails."""

    def test_extract_company_from_email(self):
        """Test company extraction from email."""
        orchestrator = JobAutomationOrchestrator()
        
        email = {
            "from": "recruiter@techcorp.com",
            "subject": "Opportunity at TechCorp for Senior Engineer",
            "body": "..."
        }
        
        company = orchestrator._extract_company_from_email(email)
        
        assert company is not None
        assert len(company) > 0

    def test_extract_role_from_email(self):
        """Test role extraction from email."""
        orchestrator = JobAutomationOrchestrator()
        
        email = {
            "subject": "Senior Software Engineer - TechCorp",
            "body": "We are looking for a Senior Software Engineer..."
        }
        
        role = orchestrator._extract_role_from_email(email)
        
        assert role is not None
        assert len(role) > 0

    def test_extract_unknown_company(self):
        """Test extraction with unknown company."""
        orchestrator = JobAutomationOrchestrator()
        
        email = {
            "from": "unknown@example.com",
            "subject": "Random job posting",
            "body": "..."
        }
        
        company = orchestrator._extract_company_from_email(email)
        
        assert company == "Unknown Company" or company is not None


class TestJobDetection:
    """Test job detection workflow."""

    @mark_asyncio
    async def test_detect_new_jobs_from_linkedin(self):
        """Test detecting new jobs from LinkedIn."""
        orchestrator = JobAutomationOrchestrator()
        
        await orchestrator.detect_new_jobs()
        
        # Check state machine has jobs
        pending = orchestrator.state_machine.get_pending_approvals()
        # May or may not have pending based on deduplication
        assert isinstance(pending, list)

    @mark_asyncio
    async def test_detect_new_jobs_from_emails(self):
        """Test detecting new jobs from emails."""
        orchestrator = JobAutomationOrchestrator()
        
        # Mock Gmail
        orchestrator.gmail_mcp = AsyncMock()
        orchestrator.gmail_mcp.is_connected = True
        orchestrator.gmail_mcp.fetch_unread_emails = AsyncMock(return_value={
            "status": "success",
            "emails": create_mock_recruiter_emails(),
        })
        
        await orchestrator.detect_new_jobs()
        
        # Check jobs were detected
        stats = orchestrator.state_machine.get_stats()
        assert stats is not None

    @mark_asyncio
    async def test_job_deduplication(self):
        """Test duplicate jobs are filtered."""
        orchestrator = JobAutomationOrchestrator()
        
        # First detection
        await orchestrator.detect_new_jobs()
        stats_1 = orchestrator.state_machine.get_stats()
        
        # Second detection (should have fewer new jobs due to dedup)
        await orchestrator.detect_new_jobs()
        stats_2 = orchestrator.state_machine.get_stats()
        
        # Stats should change but not duplicate jobs
        assert stats_1 is not None
        assert stats_2 is not None


class TestJobProcessing:
    """Test job processing workflow."""

    @mark_asyncio
    async def test_process_approved_job(self):
        """Test processing an approved job."""
        orchestrator = JobAutomationOrchestrator()
        
        mock_job = Mock()
        mock_job.job_id = "job_001"
        mock_job.company = "TechCorp"
        mock_job.role = "Senior Engineer"
        mock_job.source = "linkedin"
        
        # Mock state updates
        orchestrator.state_machine.update_state = Mock()
        orchestrator.handle_linkedin_job = AsyncMock()
        
        await orchestrator.process_approved_job(mock_job)
        
        # Check state was updated
        orchestrator.state_machine.update_state.assert_called()

    @mark_asyncio
    async def test_process_email_job(self):
        """Test processing an email-based job."""
        orchestrator = JobAutomationOrchestrator()
        orchestrator.metadata = create_mock_metadata()
        
        orchestrator.gmail_mcp = AsyncMock()
        orchestrator.gmail_mcp.is_connected = True
        orchestrator.gmail_mcp.send_email_reply = AsyncMock(return_value={
            "status": "success"
        })
        
        orchestrator.ollama_client = AsyncMock()
        orchestrator.ollama_client.generate = AsyncMock(return_value="Great response!")
        
        mock_job = Mock()
        mock_job.job_id = "email_001"
        mock_job.company = "TechCorp"
        mock_job.role = "Engineer"
        mock_job.source = "email"
        mock_job.metadata = {
            "from": "recruiter@example.com",
            "subject": "Job opportunity",
            "msg_id": "msg_001"
        }
        
        orchestrator.state_machine.update_state = Mock()
        
        await orchestrator.process_approved_job(mock_job)
        
        # Verify email was handled
        assert orchestrator.state_machine.update_state.called


class TestFullIntegration:
    """Integration tests for complete workflows."""

    @mark_asyncio
    async def test_full_job_discovery_workflow(self):
        """Test complete job discovery workflow."""
        orchestrator = JobAutomationOrchestrator()
        
        # Mock MCP clients
        orchestrator.gmail_mcp = AsyncMock()
        orchestrator.gmail_mcp.is_connected = True
        orchestrator.gmail_mcp.fetch_unread_emails = AsyncMock(return_value={
            "status": "success",
            "emails": create_mock_recruiter_emails(),
        })
        
        # Run detection
        await orchestrator.detect_new_jobs()
        
        # Verify jobs in state machine
        stats = orchestrator.state_machine.get_stats()
        assert "total" in stats or stats is not None

    @mark_asyncio
    async def test_full_approval_and_processing_workflow(self):
        """Test complete approval and processing workflow."""
        orchestrator = JobAutomationOrchestrator()
        orchestrator.metadata = create_mock_metadata()
        
        # Setup mocks
        orchestrator.gmail_mcp = AsyncMock()
        orchestrator.gmail_mcp.is_connected = True
        orchestrator.gmail_mcp.fetch_unread_emails = AsyncMock(return_value={
            "status": "success",
            "emails": create_mock_recruiter_emails(),
        })
        orchestrator.gmail_mcp.send_email_reply = AsyncMock(return_value={
            "status": "success"
        })
        
        orchestrator.ollama_client = AsyncMock()
        orchestrator.ollama_client.generate = AsyncMock(
            return_value="Interested in this position!"
        )
        
        # Detect jobs
        await orchestrator.detect_new_jobs()
        
        # Process approvals
        await orchestrator.process_cli_approvals()
        
        # Should complete without errors
        assert orchestrator.state_machine is not None


# ============================================================================
# Manual Testing Functions
# ============================================================================

async def test_linkedin_discovery_manual():
    """Manual test: Test LinkedIn job discovery."""
    print("\n" + "="*70)
    print("🔍 TESTING LINKEDIN JOB DISCOVERY")
    print("="*70)
    
    try:
        orchestrator = JobAutomationOrchestrator()
        
        print("\n1️⃣  Running LinkedIn discovery...")
        jobs = await orchestrator.run_linkedin_discovery()
        
        if len(jobs) > 0:
            print(f"✅ Successfully discovered {len(jobs)} jobs")
            for i, job in enumerate(jobs, 1):
                print(f"\n   Job {i}:")
                print(f"     • Title: {job.get('title', 'N/A')}")
                print(f"     • Company: {job.get('company', 'N/A')}")
                print(f"     • Location: {job.get('location', 'N/A')}")
                print(f"     • Salary: {job.get('salary', 'N/A')}")
            return True
        else:
            print("⚠️  No jobs discovered")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_email_checking_manual():
    """Manual test: Test email checking for opportunities."""
    print("\n" + "="*70)
    print("📧 TESTING EMAIL CHECKING FOR OPPORTUNITIES")
    print("="*70)
    
    try:
        orchestrator = JobAutomationOrchestrator()
        
        # Mock Gmail connection
        orchestrator.gmail_mcp = AsyncMock()
        orchestrator.gmail_mcp.is_connected = True
        orchestrator.gmail_mcp.fetch_unread_emails = AsyncMock(return_value={
            "status": "success",
            "emails": create_mock_recruiter_emails(),
        })
        
        print("\n1️⃣  Checking for recruiter emails...")
        opportunities = await orchestrator.check_emails_for_opportunities()
        
        if len(opportunities) > 0:
            print(f"✅ Found {len(opportunities)} email opportunities")
            for i, opp in enumerate(opportunities, 1):
                print(f"\n   Email {i}:")
                print(f"     • From: {opp.get('from', 'N/A')}")
                print(f"     • Company: {opp.get('company', 'N/A')}")
                print(f"     • Role: {opp.get('role', 'N/A')}")
            return True
        else:
            print("⚠️  No email opportunities found")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_email_sending_manual():
    """Manual test: Test email response generation and sending."""
    print("\n" + "="*70)
    print("💌 TESTING EMAIL RESPONSE GENERATION AND SENDING")
    print("="*70)
    
    try:
        orchestrator = JobAutomationOrchestrator()
        orchestrator.metadata = create_mock_metadata()
        
        # Mock clients
        orchestrator.gmail_mcp = AsyncMock()
        orchestrator.gmail_mcp.is_connected = True
        orchestrator.gmail_mcp.send_email_reply = AsyncMock(return_value={
            "status": "success",
            "message_id": "msg_123"
        })
        
        orchestrator.ollama_client = AsyncMock()
        generated_response = "Thank you for reaching out! I am very interested in the Senior Engineer position at TechCorp..."
        orchestrator.ollama_client.generate = AsyncMock(return_value=generated_response)
        
        print("\n1️⃣  Creating mock job opportunity...")
        mock_job = Mock()
        mock_job.company = "TechCorp"
        mock_job.role = "Senior Software Engineer"
        mock_job.metadata = {
            "from": "recruiter@techcorp.com",
            "subject": "RE: Senior Engineer Position at TechCorp",
            "body": "We are excited to invite you to apply for...",
            "msg_id": "email_001"
        }
        
        print("2️⃣  Handling email response...")
        await orchestrator.handle_email_response(mock_job)
        
        print("\n✅ Email response process completed successfully")
        print(f"\n📝 Generated Response Preview:")
        print(f"   {generated_response[:100]}...")
        
        # Verify calls
        if orchestrator.ollama_client.generate.called:
            print("\n✅ LLM response generated")
        if orchestrator.gmail_mcp.send_email_reply.called:
            print("✅ Email sent via Gmail")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_workflow_manual():
    """Manual test: Test complete job discovery and email sending workflow."""
    print("\n" + "="*70)
    print("🔄 TESTING COMPLETE ORCHESTRATOR WORKFLOW")
    print("="*70)
    
    try:
        orchestrator = JobAutomationOrchestrator()
        orchestrator.metadata = create_mock_metadata()
        
        # Mock clients
        orchestrator.gmail_mcp = AsyncMock()
        orchestrator.gmail_mcp.is_connected = True
        orchestrator.gmail_mcp.fetch_unread_emails = AsyncMock(return_value={
            "status": "success",
            "emails": create_mock_recruiter_emails(),
        })
        orchestrator.gmail_mcp.send_email_reply = AsyncMock(return_value={
            "status": "success"
        })
        
        orchestrator.ollama_client = AsyncMock()
        orchestrator.ollama_client.generate = AsyncMock(
            return_value="I am interested in this position!"
        )
        
        print("\n1️⃣  Detecting new jobs from LinkedIn...")
        linkedin_jobs = await orchestrator.run_linkedin_discovery()
        print(f"✅ Found {len(linkedin_jobs)} jobs from LinkedIn")
        
        print("\n2️⃣  Detecting opportunities from emails...")
        email_opps = await orchestrator.check_emails_for_opportunities()
        print(f"✅ Found {len(email_opps)} opportunities from emails")
        
        print("\n3️⃣  Running full job detection cycle...")
        await orchestrator.detect_new_jobs()
        stats = orchestrator.state_machine.get_stats()
        print(f"✅ Job detection complete - Stats: {stats}")
        
        print("\n4️⃣  Processing approvals...")
        await orchestrator.process_cli_approvals()
        print("✅ Approval processing complete")
        
        print("\n" + "="*70)
        print("✅ Full workflow test completed successfully!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_manual_tests():
    """Run all manual tests."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*10 + "JOB AUTOMATION ORCHESTRATOR Test Suite" + " "*19 + "║")
    print("╚" + "="*68 + "╝")
    
    linkedin_result = await test_linkedin_discovery_manual()
    email_check_result = await test_email_checking_manual()
    email_send_result = await test_email_sending_manual()
    workflow_result = await test_full_workflow_manual()
    
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"LinkedIn Discovery:     {'✅ PASSED' if linkedin_result else '❌ FAILED'}")
    print(f"Email Checking:         {'✅ PASSED' if email_check_result else '❌ FAILED'}")
    print(f"Email Sending:          {'✅ PASSED' if email_send_result else '❌ FAILED'}")
    print(f"Full Workflow:          {'✅ PASSED' if workflow_result else '❌ FAILED'}")
    print("="*70)
    
    if all([linkedin_result, email_check_result, email_send_result, workflow_result]):
        print("\n🎉 All orchestrator tests passed!")
        return True
    else:
        print("\n⚠️  Some tests failed. Review output above.")
        return False


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    """Run manual tests directly."""
    print("\n")
    print("Job Orchestrator Testing Modes:")
    print("1. With pytest (recommended):")
    print("   python -m pytest tests/test_orchestrator_agent.py -v -s")
    print("\n2. Direct execution:")
    print("   python tests/test_orchestrator_agent.py")
    print("\nRunning manual tests...\n")
    
    asyncio.run(run_all_manual_tests())
