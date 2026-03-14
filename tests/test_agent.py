"""
Sample test file for job automation agent.

Run with: python -m pytest tests/test_agent.py -v
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.deduplication import JobDeduplicator
from utils.state_machine import JobStateMachine, JobState


class TestJobDeduplicator:
    """Test deduplication logic."""

    def test_exact_duplicate(self):
        """Test detection of exact duplicates."""
        dedup = JobDeduplicator(similarity_threshold=0.85)

        # Add first job
        dedup.add_job("TechCorp", "Software Engineer")

        # Check for duplicate
        assert dedup.is_duplicate("TechCorp", "Software Engineer") is True

    def test_fuzzy_match(self):
        """Test fuzzy matching above threshold."""
        dedup = JobDeduplicator(similarity_threshold=0.85)

        dedup.add_job("TechCorp", "Engineer")

        # Similar but different
        assert dedup.is_duplicate("TechCorp", "Software Engineer") is True

    def test_no_match(self):
        """Test non-matching jobs."""
        dedup = JobDeduplicator(similarity_threshold=0.85)

        dedup.add_job("Company A", "Role A")

        # Completely different
        assert dedup.is_duplicate("Company B", "Role B") is False

    def test_cache_stats(self):
        """Test cache statistics."""
        dedup = JobDeduplicator()

        dedup.add_job("Company", "Role")
        stats = dedup.get_stats()

        assert stats["cached_jobs"] == 1


class TestJobStateMachine:
    """Test job state machine."""

    def test_job_creation(self):
        """Test job creation."""
        state_machine = JobStateMachine()

        job = state_machine.create_job(
            job_id="test_001",
            company="TestCorp",
            role="Engineer",
        )

        assert job.job_id == "test_001"
        assert job.state == JobState.DETECTED

    def test_state_transition(self):
        """Test state transitions."""
        state_machine = JobStateMachine()

        job_id = "test_001"
        state_machine.create_job(job_id, "TestCorp", "Engineer")

        # Transition to CLI_PENDING
        assert state_machine.update_state(job_id, JobState.CLI_PENDING) is True

        job = state_machine.get_job(job_id)
        assert job.state == JobState.CLI_PENDING

    def test_get_pending_approvals(self):
        """Test getting pending approvals."""
        state_machine = JobStateMachine()

        # Create multiple jobs
        state_machine.create_job("job_001", "Company1", "Role1")
        state_machine.create_job("job_002", "Company2", "Role2")

        # Move first to CLI_PENDING
        state_machine.update_state("job_001", JobState.CLI_PENDING)

        pending = state_machine.get_pending_approvals()
        assert len(pending) == 1
        assert pending[0].job_id == "job_001"

    def test_job_stats(self):
        """Test job statistics."""
        state_machine = JobStateMachine()

        state_machine.create_job("job_001", "Company", "Role")
        state_machine.update_state("job_001", JobState.APPROVED)

        state_machine.create_job("job_002", "Company", "Role")
        state_machine.update_state("job_002", JobState.FAILED)

        stats = state_machine.get_stats()
        assert stats[JobState.DETECTED.value] == 0
        assert stats[JobState.APPROVED.value] == 1
        assert stats[JobState.FAILED.value] == 1


class TestEncryption:
    """Test encryption utilities."""

    @pytest.mark.skip(reason="Requires interactive password input")
    def test_metadata_encryption(self):
        """Test metadata encryption and decryption."""
        from utils.encryption import ConfigEncryption

        encryption = ConfigEncryption()

        test_data = {
            "name": "Test User",
            "email": "test@example.com",
        }

        password = "secure_password_123"

        # Encrypt
        encrypted = encryption.encrypt_metadata(test_data, password)
        assert encrypted is not None

        # Decrypt
        decrypted = encryption.decrypt_metadata(encrypted, password)
        assert decrypted["name"] == test_data["name"]


# Run tests with: python -m pytest tests/ -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
