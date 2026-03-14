"""Configuration models for the job automation system."""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from pathlib import Path
import os


class PersonalInfo(BaseModel):
    """User personal information."""

    name: str
    email: str
    phone: str
    first_name: str
    last_name: str
    resume_path: str


class WorkHistory(BaseModel):
    """Work history entry."""

    company: str
    position: str
    duration: str
    description: str


class AccountInfo(BaseModel):
    """Account information for job portals."""

    site: str
    email: str
    password_encrypted: str


class MetadataContent(BaseModel):
    """Complete metadata structure."""

    personal_info: PersonalInfo
    work_history: List[WorkHistory] = []
    skills: List[str] = []
    cover_letter_template: str = ""
    accounts_created: List[AccountInfo] = []

    class Config:
        validate_assignment = True


class SystemConfig(BaseModel):
    """System configuration."""

    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    )
    ollama_timeout: float = 300.0

    # Gmail settings
    gmail_address: str = Field(default_factory=lambda: os.getenv("GMAIL_ADDRESS", ""))
    gmail_app_password: str = Field(
        default_factory=lambda: os.getenv("GMAIL_APP_PASSWORD", "")
    )
    gmail_poll_interval: int = 30  # seconds

    # LinkedIn settings
    linkedin_email: str = Field(default_factory=lambda: os.getenv("LINKEDIN_EMAIL", ""))
    linkedin_password: str = Field(
        default_factory=lambda: os.getenv("LINKEDIN_PASSWORD", "")
    )
    linkedin_run_interval: int = 20 * 60  # 20 minutes

    # Deduplication settings
    dedup_similarity_threshold: float = 0.85  # 85% fuzzy match

    # Job state settings
    job_processing_timeout: int = 3600  # 1 hour

    # Metadata file
    metadata_file: str = Field(
        default_factory=lambda: os.path.expanduser(
            os.getenv("METADATA_FILE", "~/.llm_agent/metadata.json")
        )
    )

    # MCP server settings
    gmail_mcp_endpoint: str = "stdio"
    linkedin_mcp_endpoint: str = "stdio"
    jobportal_mcp_endpoint: str = "stdio"

    # Logging
    log_file: str = "logs/orchestrator.log"
    log_level: str = "DEBUG"
    log_rotation: str = "10 MB"
    log_retention: int = 3

    @validator("gmail_address", "gmail_app_password", pre=True)
    def validate_gmail_settings(cls, v):
        if not v:
            raise ValueError("Gmail settings required via environment variables")
        return v

    @validator("metadata_file", pre=True)
    def validate_metadata_file(cls, v):
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)


class CLIApprovalConfig(BaseModel):
    """Configuration for CLI approval workflow."""

    enabled: bool = True
    require_approval: bool = True
    auto_approve_duplicates: bool = False
    timeout_seconds: Optional[int] = None  # No timeout
