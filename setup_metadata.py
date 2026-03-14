"""Generate sample encrypted metadata for local agent."""

import json
import sys
from pathlib import Path
from utils.encryption import ConfigEncryption


SAMPLE_METADATA = {
    "personal_info": {
        "name": "Your Name",
        "email": "your.email@gmail.com",
        "phone": "+1-555-0100",
        "first_name": "Your",
        "last_name": "Name",
        "resume_path": "/path/to/your/resume.pdf",
    },
    "work_history": [
        {
            "company": "Tech Company A",
            "position": "Software Engineer",
            "duration": "2021-2023",
            "description": "Built scalable backend services using Python and PostgreSQL",
        },
        {
            "company": "Startup B",
            "position": "Full Stack Engineer",
            "duration": "2020-2021",
            "description": "Developed web applications with React and Node.js",
        },
    ],
    "skills": [
        "Python",
        "JavaScript",
        "PostgreSQL",
        "Docker",
        "AWS",
        "Machine Learning",
        "System Design",
        "Agile/Scrum",
    ],
    "cover_letter_template": "I am excited about the opportunity to join your team as a [POSITION] at [COMPANY]...",
    "accounts_created": [],
}


def main():
    """Create encrypted metadata file."""
    try:
        # Create encryption handler
        encryption = ConfigEncryption()

        # Prepare metadata dir
        metadata_dir = Path.home() / ".llm_agent"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = metadata_dir / "metadata.json"

        print("=" * 70)
        print("🔐 JOB AUTOMATION AGENT - METADATA SETUP")
        print("=" * 70)

        # Customize metadata
        print("\nMetadata Customization:")
        print("-" * 70)

        name = (
            input(
                f"Your name [{SAMPLE_METADATA['personal_info']['name']}]: "
            ).strip()
            or SAMPLE_METADATA["personal_info"]["name"]
        )

        email = (
            input(
                f"Your email [{SAMPLE_METADATA['personal_info']['email']}]: "
            ).strip()
            or SAMPLE_METADATA["personal_info"]["email"]
        )

        phone = (
            input(
                f"Your phone [{SAMPLE_METADATA['personal_info']['phone']}]: "
            ).strip()
            or SAMPLE_METADATA["personal_info"]["phone"]
        )

        resume_path = (
            input(
                f"Resume path [{SAMPLE_METADATA['personal_info']['resume_path']}]: "
            ).strip()
            or SAMPLE_METADATA["personal_info"]["resume_path"]
        )

        # Update metadata
        SAMPLE_METADATA["personal_info"]["name"] = name
        SAMPLE_METADATA["personal_info"]["first_name"] = name.split()[0]
        SAMPLE_METADATA["personal_info"]["last_name"] = " ".join(name.split()[1:])
        SAMPLE_METADATA["personal_info"]["email"] = email
        SAMPLE_METADATA["personal_info"]["phone"] = phone
        SAMPLE_METADATA["personal_info"]["resume_path"] = resume_path

        # Get master password
        print("\n" + "-" * 70)
        print("Master Password Setup:")
        print("This password will encrypt your metadata file.")
        print("You'll need to enter it when starting the agent.")

        password = ConfigEncryption.prompt_master_password()
        if not password:
            print("❌ Password cannot be empty")
            return False

        password_confirm = ConfigEncryption.prompt_master_password_confirm()
        if password != password_confirm:
            print("❌ Passwords do not match")
            return False

        # Encrypt metadata
        encrypted_data = encryption.encrypt_metadata(SAMPLE_METADATA, password)

        # Save to file
        with open(metadata_file, "w") as f:
            f.write(encrypted_data)

        # Set restrictive permissions
        import os

        os.chmod(metadata_file, 0o600)

        print("\n" + "=" * 70)
        print("✅ METADATA SETUP COMPLETE")
        print("=" * 70)
        print(f"Metadata file: {metadata_file}")
        print(f"Permissions: 600 (read/write owner only)")
        print("\nEnvironment setup:")
        print("  export METADATA_FILE='~/.llm_agent/metadata.json'")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


# Add helper for password confirmation
def prompt_master_password_confirm() -> str:
    """Prompt user for master password confirmation."""
    import getpass

    return getpass.getpass("Confirm master password: ")


# Monkey-patch for convenience
ConfigEncryption.prompt_master_password_confirm = staticmethod(
    prompt_master_password_confirm
)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
