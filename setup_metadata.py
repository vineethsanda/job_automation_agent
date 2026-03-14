#!/usr/bin/env python3
"""Generate metadata from resume PDF."""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from config.models import MetadataContent, PersonalInfo, WorkHistory
from utils.encryption import ConfigEncryption

try:
    from pypdf import PdfReader
except ImportError:
    print("❌ pypdf not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
    from pypdf import PdfReader


def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Failed to extract PDF text: {e}")
        return ""


def parse_resume(text: str) -> dict:
    """Parse resume text to extract structured information."""
    lines = text.split('\n')
    
    # Simple parsing - look for common resume sections
    data = {
        "name": "",
        "email": "",
        "phone": "",
        "skills": [],
        "work_history": [],
    }
    
    # Extract name (usually first line)
    if lines:
        potential_name = lines[0].strip()
        if len(potential_name.split()) >= 2:
            data["name"] = potential_name
    
    # Extract email and phone
    for line in lines[:20]:  # Check first 20 lines
        line_lower = line.lower()
        if "email" in line_lower or "@" in line:
            email = line.split(":")[-1].strip() if ":" in line else line.strip()
            if "@" in email:
                data["email"] = email.replace("Email: ", "").replace("email: ", "").strip()
        
        if "phone" in line_lower or "contact" in line_lower:
            phone = line.split(":")[-1].strip() if ":" in line else ""
            if phone and any(c.isdigit() for c in phone):
                data["phone"] = phone.replace("Phone: ", "").replace("phone: ", "").strip()
    
    # Extract skills section
    in_skills = False
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if "skill" in line_lower:
            in_skills = True
            continue
        elif in_skills and line.strip() and any(x in line_lower for x in ["experience", "education", "work", "project"]):
            in_skills = False
        elif in_skills and line.strip():
            # Parse skills
            skills_text = line.strip()
            if ":" in skills_text:
                skills_text = skills_text.split(":")[-1]
            # Split by comma or semicolon
            skills = [s.strip() for s in skills_text.replace(";", ",").split(",")]
            data["skills"].extend([s for s in skills if s])
    
    # Extract work history
    in_work = False
    current_job = {}
    
    for line in lines:
        line_lower = line.lower()
        
        if any(x in line_lower for x in ["experience", "work history", "professional experience"]):
            in_work = True
            continue
        elif in_work and any(x in line_lower for x in ["education", "skills", "project", "certification"]):
            if current_job:
                data["work_history"].append(current_job)
            in_work = False
            current_job = {}
        
        if in_work and line.strip():
            line = line.strip()
            
            # Try to identify company/position
            if " - " in line or " at " in line:
                parts = line.split(" - " if " - " in line else " at ")
                if len(parts) >= 2:
                    if current_job:
                        data["work_history"].append(current_job)
                    current_job = {
                        "company": parts[-1].strip(),
                        "position": parts[0].strip(),
                        "duration": "",
                        "description": ""
                    }
            elif current_job and any(c.isdigit() for c in line):
                # Likely a date/duration line
                current_job["duration"] = line
            elif current_job and not line.startswith(" "):
                # New job entry
                if current_job:
                    data["work_history"].append(current_job)
                current_job = {
                    "company": "",
                    "position": line,
                    "duration": "",
                    "description": ""
                }
    
    if current_job:
        data["work_history"].append(current_job)
    
    # Clean up duplicates
    data["skills"] = list(set(s.lower() for s in data["skills"] if s))[:20]
    
    return data


async def generate_metadata(resume_path: str) -> bool:
    """Generate encrypted metadata from resume."""
    
    print("\n" + "="*70)
    print("📄 RESUME METADATA GENERATOR")
    print("="*70 + "\n")
    
    # Check file exists
    if not Path(resume_path).exists():
        print(f"❌ Resume file not found: {resume_path}")
        return False
    
    print(f"📖 Extracting text from: {resume_path}")
    pdf_text = extract_pdf_text(resume_path)
    
    if not pdf_text:
        print("❌ Failed to extract text from PDF")
        return False
    
    print(f"✅ Extracted {len(pdf_text)} characters\n")
    
    # Parse resume
    print("🔍 Parsing resume content...")
    parsed = parse_resume(pdf_text)
    
    # Prompt user to verify/edit
    print("\n" + "="*70)
    print("EXTRACTED INFORMATION")
    print("="*70)
    
    print(f"\n📝 Name: {parsed['name']}")
    if not parsed['name']:
        parsed['name'] = input("Enter your full name: ").strip()
    
    print(f"📧 Email: {parsed['email']}")
    if not parsed['email']:
        parsed['email'] = input("Enter your email: ").strip()
    
    print(f"📱 Phone: {parsed['phone']}")
    if not parsed['phone']:
        parsed['phone'] = input("Enter your phone number: ").strip()
    
    print(f"\n🛠️  Skills ({len(parsed['skills'])} found):")
    for skill in parsed['skills'][:10]:
        print(f"  • {skill}")
    if len(parsed['skills']) > 10:
        print(f"  ... and {len(parsed['skills']) - 10} more")
    
    print(f"\n💼 Work History ({len(parsed['work_history'])} entries):")
    for job in parsed['work_history'][:3]:
        print(f"  • {job['position']} at {job['company']} ({job['duration']})")
    if len(parsed['work_history']) > 3:
        print(f"  ... and {len(parsed['work_history']) - 3} more")
    
    # Create metadata object
    print("\n" + "="*70)
    print("CREATING METADATA")
    print("="*70 + "\n")
    
    # Split name
    name_parts = parsed['name'].split()
    first_name = name_parts[0] if name_parts else "User"
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
    
    personal_info = PersonalInfo(
        name=parsed['name'],
        email=parsed['email'],
        phone=parsed['phone'],
        first_name=first_name,
        last_name=last_name,
        resume_path=resume_path
    )
    
    work_history = [
        WorkHistory(
            company=job['company'],
            position=job['position'],
            duration=job['duration'],
            description=job['description']
        )
        for job in parsed['work_history']
        if job['company'] and job['position']
    ]
    
    metadata = MetadataContent(
        personal_info=personal_info,
        work_history=work_history,
        skills=parsed['skills'],
        cover_letter_template="",
        accounts_created=[]
    )
    
    print(f"✅ Created metadata for: {parsed['name']}")
    print(f"   Email: {parsed['email']}")
    print(f"   Phone: {parsed['phone']}")
    print(f"   Skills: {len(parsed['skills'])}")
    print(f"   Work History: {len(work_history)}")
    
    # Encrypt and save
    print("\n" + "="*70)
    print("ENCRYPTING & SAVING METADATA")
    print("="*70 + "\n")
    
    encryption = ConfigEncryption()
    
    # Get or create master password
    print("🔐 You need to set a master password for encryption")
    print("   (This encrypts your personal data)")
    
    password = ConfigEncryption.prompt_master_password()
    
    try:
        # Convert to dict for encryption
        metadata_dict = metadata.dict()
        
        # Encrypt
        encrypted_data = encryption.encrypt_metadata(metadata_dict, password)
        
        # Create metadata directory if needed
        metadata_path = Path.home() / ".llm_agent"
        metadata_path.mkdir(parents=True, exist_ok=True)
        
        metadata_file = metadata_path / "metadata.json"
        
        # Save encrypted metadata
        with open(metadata_file, "w") as f:
            f.write(encrypted_data)
        
        print(f"\n✅ Metadata saved to: {metadata_file}")
        print(f"   File size: {len(encrypted_data)} bytes (encrypted)")
        print(f"\n🎉 Setup complete! Your metadata is now encrypted and secure.")
        print(f"\n💡 The agent will use this metadata to:")
        print(f"   • Generate personalized email replies")
        print(f"   • Fill out job application forms")
        print(f"   • Match your skills to job opportunities")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to encrypt metadata: {e}")
        return False


async def main():
    """Main entry point."""
    resume_path = "/Users/sandavineeth/Desktop/vineeth_sanda_resume.pdf"
    
    success = await generate_metadata(resume_path)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
