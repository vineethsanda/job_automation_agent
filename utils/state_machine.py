"""Job state machine for tracking automation progress."""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict, field
import json
from loguru import logger


class JobState(str, Enum):
    """Job processing states."""

    DETECTED = "DETECTED"  # Initial discovery
    CLI_PENDING = "CLI_PENDING"  # Waiting for human approval
    APPROVED = "APPROVED"  # User approved
    PROCESSING = "PROCESSING"  # Active work
    COMPLETED = "COMPLETED"  # Success
    FAILED = "FAILED"  # Error occurred


@dataclass
class Job:
    """Job representation with state and metadata."""

    job_id: str
    company: str
    role: str
    state: JobState = JobState.DETECTED
    url: Optional[str] = None
    source: str = "unknown"  # linkedin, jobportal, etc.
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    approval_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["state"] = self.state.value
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.approval_at:
            data["approval_at"] = self.approval_at.isoformat()
        if self.completed_at:
            data["completed_at"] = self.completed_at.isoformat()
        return data

    def set_state(self, new_state: JobState, error: Optional[str] = None) -> None:
        """Update job state with timestamp."""
        self.state = new_state
        self.updated_at = datetime.utcnow()
        if error:
            self.error_message = error
        if new_state == JobState.APPROVED:
            self.approval_at = datetime.utcnow()
        if new_state in (JobState.COMPLETED, JobState.FAILED):
            self.completed_at = datetime.utcnow()
        logger.info(
            f"Job {self.job_id} transitioned to {new_state.value} "
            f"({self.company}/{self.role})"
        )


class JobStateMachine:
    """Manage job state transitions."""

    def __init__(self):
        self.jobs: Dict[str, Job] = {}

    def create_job(
        self,
        job_id: str,
        company: str,
        role: str,
        url: Optional[str] = None,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Job:
        """Create a new job."""
        job = Job(
            job_id=job_id,
            company=company,
            role=role,
            url=url,
            source=source,
            metadata=metadata or {},
        )
        self.jobs[job_id] = job
        logger.info(f"Created job {job_id}: {company}/{role}")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self.jobs.get(job_id)

    def update_state(
        self,
        job_id: str,
        new_state: JobState,
        error: Optional[str] = None,
    ) -> bool:
        """Update job state."""
        job = self.jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False

        job.set_state(new_state, error)
        return True

    def get_pending_approvals(self) -> list[Job]:
        """Get all jobs awaiting CLI approval."""
        return [j for j in self.jobs.values() if j.state == JobState.CLI_PENDING]

    def get_by_state(self, state: JobState) -> list[Job]:
        """Get all jobs in a specific state."""
        return [j for j in self.jobs.values() if j.state == state]

    def get_stats(self) -> Dict[str, int]:
        """Get job statistics."""
        return {state.value: len(self.get_by_state(state)) for state in JobState}
