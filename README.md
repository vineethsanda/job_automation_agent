# Job Automation Agent - Complete Setup Guide

**Local LLM Job Automation System for Mac mini M4**

This is a complete, production-ready job automation system using Llama 3.1 8B via Ollama for local inference. It features dedicated MCP servers, CLI-based human approval, LinkedIn stealth automation, and encrypted credential management.

## Architecture Overview

```
orchestrator/agent.py (Main asyncio loop)
├── utils/
│   ├── encryption.py (Metadata decryption via CLI password)
│   ├── deduplication.py (Fuzzy matching ≥85% similarity)
│   ├── state_machine.py (Job: DETECTED → CLI_PENDING → APPROVED → PROCESSING → COMPLETED/FAILED)
│   └── ollama_client.py (Local LLM via Ollama, 32K context)
├── orchestrator/
│   ├── cli_approval.py (Human-in-the-loop approval workflow)
│   └── agent.py (Main orchestrator)
└── mcp_servers/
    ├── gmail_mcp/
    │   ├── server.py (FastMCP instance)
    │   ├── tools/ (fetch_unread, send_reply, read_thread, extract_otp)
    │   └── utils/ (imap_client, smtp_client)
    ├── linkedin_mcp/
    │   ├── server.py (FastMCP instance)
    │   ├── tools/ (fetch_posts, extract_recruiter_email, session_manager)
    │   └── utils/ (stealth_browser, cookie_store)
    └── jobportal_mcp/
        ├── server.py (FastMCP instance)
        ├── tools/ (create_account, fill_application, handle_redirect)
        └── utils/ (form_filler, otp_handler)
```

## System Requirements

- **Hardware**: Mac mini M4
- **OS**: macOS 13+
- **Python**: 3.11+
- **Memory**: 8GB minimum (16GB recommended)
- **Internet**: Required for job site access

## Installation

### 1. Install Python 3.11+

```bash
# Check Python version
python3 --version

# If not installed, use Homebrew
brew install python@3.11
```

### 2. Install Ollama

```bash
# Download from https://ollama.ai
# Or use Homebrew
brew install ollama

# Pull Llama 3.1 8B model
ollama pull llama2:latest

# Or for Llama 3.1 specifically if available:
# ollama pull llama3.1:8b
```

### 3. Clone/Create Project

```bash
cd ~/Desktop/llm

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 4. Setup Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Generate app password (16-character token)
4. Copy the password

### 5. Configure Environment

```bash
# Copy example to .env
cp .env.example .env

# Edit .env with your values
# For Gmail:
#   GMAIL_ADDRESS=your@gmail.com
#   GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx (your 16-char app password)
# For LinkedIn (optional):
#   LINKEDIN_EMAIL=your@gmail.com
#   LINKEDIN_PASSWORD=your-password

nano .env
```

### 6. Setup Metadata

```bash
# Run setup script
python3 setup_metadata.py

# Follow prompts:
# - Enter your name
# - Enter your email
# - Enter your phone
# - Enter path to your resume
# - Create master password (you'll need this to run the agent)

# This creates:
# ~/.llm_agent/
# ├── metadata.json (encrypted)
# └── salt (for key derivation)
```

## Running the System

### Option 1: Full System (All MCP Servers + Orchestrator)

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Gmail MCP Server
cd ~/Desktop/llm
source venv/bin/activate
export GMAIL_ADDRESS="your@gmail.com"
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
python3 -m mcp_servers.gmail_mcp.server

# Terminal 3: Start LinkedIn MCP Server
export LINKEDIN_EMAIL="your@gmail.com"
export LINKEDIN_PASSWORD="your-password"
python3 -m mcp_servers.linkedin_mcp.server

# Terminal 4: Start Job Portal MCP Server
export METADATA_FILE="~/.llm_agent/metadata.json"
python3 -m mcp_servers.jobportal_mcp.server

# Terminal 5: Start Orchestrator
python3 orchestrator/agent.py
```

### Option 2: Development Mode (Orchestrator Only + Mock MCP)

```bash
source venv/bin/activate
python3 orchestrator/agent.py

# The system will prompt for master password
# Then start the main approval loop
```

## Usage Workflow

### Email-Based Job Discovery

1. **Recruiter sends email**: Recruiter contacts you via Gmail with job opportunity
2. **Agent detects**: Orchestrator polls Gmail (30s interval) for unread emails
3. **CLI approval**: Agent displays job details and waits for your approval
   - Options: `[y]` approve, `[n]` reject, `[v]` view details
4. **Processing**: 
   - If approved: Generate personalized response using Ollama
   - Send reply via Gmail MCP
   - Log as completed
5. **Deduplication**: Fuzzy matching prevents duplicate applications (≥85% similarity on company+role)

### LinkedIn Job Discovery

1. **Stealth browse**: LinkedIn MCP uses Playwright with human-like behavior
   - Randomized delays (2-8s between actions)
   - Mouse movements and viewport scrolling
   - Cookie persistence in `/tmp/linkedin_session/`
2. **20-minute cron**: Minimum 20-minute interval between runs
3. **Job extraction**: Parse job posts (top 10)
4. **CLI approval**: Same workflow as email jobs
5. **Application**: Either send message or redirect to job portal

### Job Portal Application

1. **Account creation**: jobportal_mcp creates account with sanitized credentials
2. **OTP handling**: gmail_mcp extracts OTP from email within 2-minute window
3. **Form filling**: Playwright fills form with data from metadata
4. **Resume upload**: Attach resume from metadata path
5. **Submission**: Click submit and wait for confirmation

## File Structure

```
design
├── orchestrator/
│   ├── agent.py              # Main orchestrator loop
│   ├── cli_approval.py       # CLI approval interface
│   └── __init__.py
├── mcp_servers/
│   ├── gmail_mcp/
│   │   ├── server.py
│   │   ├── tools/
│   │   │   ├── fetch_unread.py
│   │   │   ├── send_reply.py
│   │   │   ├── read_thread.py
│   │   │   └── extract_otp.py
│   │   ├── utils/
│   │   │   ├── imap_client.py
│   │   │   └── smtp_client.py
│   │   └── __init__.py
│   ├── linkedin_mcp/
│   │   ├── server.py
│   │   ├── tools/
│   │   │   ├── fetch_posts.py
│   │   │   ├── extract_recruiter_email.py
│   │   │   └── session_manager.py
│   │   ├── utils/
│   │   │   ├── stealth_browser.py   # Human behavior simulation
│   │   │   └── cookie_store.py      # Plaintext session storage
│   │   └── __init__.py
│   └── jobportal_mcp/
│       ├── server.py
│       ├── tools/
│       │   ├── create_account.py
│       │   ├── fill_application.py
│       │   └── handle_redirect.py
│       ├── utils/
│       │   ├── form_filler.py
│       │   └── otp_handler.py
│       └── __init__.py
├── config/
│   ├── models.py             # Pydantic config models
│   └── __init__.py
├── utils/
│   ├── encryption.py         # CLI-based metadata decryption
│   ├── deduplication.py      # Fuzzy matching dedup
│   ├── state_machine.py      # Job state machine
│   ├── ollama_client.py      # Local LLM client
│   └── __init__.py
├── orchestrator/
│   └── agent.py              # Main agent
├── setup_metadata.py         # Metadata setup wizard
├── requirements.txt
├── .env.example
└── README.md
```

## Key Features

### 🔐 Security & Privacy

- **Encrypted metadata**: All sensitive data encrypted at rest using PBKDF2
- **CLI master password**: Decryption on startup only
- **Plaintext session storage**: LinkedIn cookies in `/tmp/linkedin_session/` with 600 permissions
- **Env vars for credentials**: GMAIL_ADDRESS, GMAIL_APP_PASSWORD via environment
- **No cloud services**: 100% local computation, no external API calls for LLM

### 🤖 Human Behavior Simulation (LinkedIn)

- Randomized action delays (2-8 seconds)
- Mouse movement simulation before clicks
- Viewport scrolling with pauses
- Chrome stealth patches to disable `navigator.webdriver`
- User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X...)
- Persistent session cookies

### ✅ State Machine & CLI Approval

Jobs flow through states:
1. **DETECTED**: Found on job site or email
2. **CLI_PENDING**: Waiting for user approval (blocks thread)
3. **APPROVED**: User approved via CLI
4. **PROCESSING**: Active work (application/email)
5. **COMPLETED**: Success
6. **FAILED**: Error or rejected

CLI interface provides:
- Batch actions: approve all, reject all, manual review
- Detail viewing with `[v]` option
- Per-job yes/no confirmation

### 🎯 Deduplication

- Fuzzy matching on company + role
- Similarity threshold: 85% (configurable)
- In-memory cache with token set ratio
- Prevents duplicate applications

### 📧 Email Integration

- **IMAP**: Fetch unread emails (30-second polling)
- **IMAP IDLE not used**: Simple polling for reliability
- **OTP extraction**: 2-minute auto-read window with regex patterns
- **SMTP replies**: Send personalized responses
- **Thread context**: Read last 7 emails from thread

### 🧠 Local LLM (Ollama)

- **Model**: Llama 3.1 8B (or llama2:latest)
- **Context**: 32K tokens
- **Output**: Structured JSON mode
- **Prompts**: Email responses, job analysis, form filling

### 📊 Logging

- **loguru**: Structured logging with rotation
- **Rotation**: 10MB per file
- **Retention**: 3 backups
- **Logs**: `logs/orchestrator.log`, `logs/gmail_mcp.log`, etc.

## Configuration Reference

### SystemConfig (orchestrator)

```python
# Ollama
ollama_base_url = "http://localhost:11434"
ollama_model = "llama2:latest"  # or "llama3.1:8b"
ollama_timeout = 300

# Gmail
gmail_address = os.getenv("GMAIL_ADDRESS")
gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
gmail_poll_interval = 30  # seconds

# LinkedIn
linkedin_email = os.getenv("LINKEDIN_EMAIL")
linkedin_password = os.getenv("LINKEDIN_PASSWORD")
linkedin_run_interval = 1200  # 20 minutes

# Deduplication
dedup_similarity_threshold = 0.85  # 85%

# Files
metadata_file = os.path.expanduser(os.getenv("METADATA_FILE", "~/.llm_agent/metadata.json"))
log_file = "logs/orchestrator.log"
log_level = "DEBUG"
log_rotation = "10 MB"
log_retention = 3
```

## Troubleshooting

### "IMAP connection failed"

- Verify `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` in `.env`
- Ensure you generated an app password (not your account password)
- Check 2FA is enabled on your Google account

### "No session found for LinkedIn"

- Run the browser login flow first: `session_action("load")`
- Or run LinkedIn MCP server in headless=False mode temporarily to log in

### "OTP extraction timeout"

- Check email is being received
- Verify `extract_otp.py` regex patterns match your OTP format
- Increase timeout_seconds parameter

### "Ollama connection refused"

- Ensure `ollama serve` is running in a separate terminal
- Check `OLLAMA_BASE_URL` points to correct address
- Verify model is downloaded: `ollama list`

### "Playwright browser hangs"

- Kill any stuck browser processes: `pkill -f chromium`
- Increase timeout values in playwright calls
- Check system has adequate free memory

## Performance Tuning

### For Mac mini M4

```python
# Increase context window (if model supports)
ollama_context = 32000

# Reduce polling interval for faster job detection
gmail_poll_interval = 15  # seconds (min 10)

# Increase browser timeout if network is slow
page_timeout = 30000  # milliseconds

# Parallel job processing
# Currently processes 1 job at a time for safety
# Can be parallelized with asyncio.gather() for multiple portals
```

## Advanced Usage

### Batch Mode

```bash
# Skip CLI approvals for testing
# (Modify CLIApprovalConfig in orchestrator/agent.py)
approval_config.require_approval = False
```

### Custom LLM Prompts

Edit `_build_email_prompt()` in `orchestrator/agent.py`:

```python
def _build_email_prompt(self, job) -> str:
    # Customize prompt for your style
```

### Multi-Account Support

Metadata JSON can store multiple accounts:

```json
{
  "accounts_created": [
    {"site": "Indeed", "email": "acc1@gmail.com", "password_encrypted": "..."},
    {"site": "LinkedIn", "email": "acc2@gmail.com", "password_encrypted": "..."}
  ]
}
```

## Safety Notes

⚠️ **LinkedIn Terms & Conditions**: This automation simulates human behavior but may violate LinkedIn's Terms of Service. Use at your own risk.

⚠️ **Rate Limiting**: 20-minute minimum interval between LinkedIn crawl runs to avoid detection.

⚠️ **Credentials Storage**: Plaintext passwords in metadata. Ensure file permissions are 600 (owner read/write only).

⚠️ **Email Security**: GMAIL_APP_PASSWORD in environment variables. Use separate environment for production.

## License

MIT License - Use at your own risk

## Support

For issues:
1. Check `logs/orchestrator.log` for error messages
2. Enable DEBUG logging: `log_level = "DEBUG"`
3. Test individual MCP servers separately
4. Verify all environment variables are set

---

**Built for Mac mini M4 with Llama 3.1 8B via Ollama**
