# Quick Reference Guide - Job Automation Agent

## Quick Start

```bash
# 1. Setup
./setup.sh

# 2. Configure
nano .env
python3 setup_metadata.py

# 3. Run
./start_agent.sh orchestrator
```

## Key Directories

| Path | Purpose |
|------|---------|
| `orchestrator/agent.py` | Main event loop |
| `mcp_servers/gmail_mcp/` | Email management |
| `mcp_servers/linkedin_mcp/` | LinkedIn job discovery |
| `mcp_servers/jobportal_mcp/` | Job application automation |
| `utils/` | Shared utilities (encryption, dedup, state machine) |
| `logs/` | Agent logs |
| `~/.llm_agent/` | Encrypted metadata & session cookies |

## Important Commands

### Setup & Config
```bash
./setup.sh                           # Initial setup
python3 setup_metadata.py            # Configure metadata
cp .env.example .env                 # Create environment
nano .env                            # Edit env vars
```

### Running
```bash
./start_agent.sh orchestrator        # Start main agent
./start_agent.sh full                # Start all services (multi-terminal)
source venv/bin/activate             # Activate virtual env
```

### Testing
```bash
python -m pytest tests/ -v           # Run tests
python -m pytest tests/test_agent.py::TestJobDeduplicator -v
```

### Utilities
```bash
tail -f logs/orchestrator.log        # Watch logs
rm ~/.llm_agent/metadata.json        # Reset metadata
rm /tmp/linkedin_session/*           # Clear LinkedIn session
```

## State Machine Flow

```
DETECTED
   ↓
CLI_PENDING ← (User chooses: y/n)
   ↓
APPROVED
   ↓
PROCESSING
   ├→ COMPLETED (success)
   └→ FAILED (error)
```

## Email Workflow

1. Check unread emails every 30 seconds
2. Parse subject for job keywords
3. CREATE job with EMAIL source
4. Move to CLI_PENDING
5. **Wait for user approval**
6. If approved: Generate response with Ollama
7. Send reply via Gmail MCP
8. Mark as COMPLETED

## LinkedIn Workflow

1. Cron every 20 minutes (rate limited)
2. Use stealth browser (human-like delays)
3. Parse job posts from feed
4. Extract company + role
5. Check fuzzy deduplication (≥85%)
6. CREATE job with LINKEDIN source
7. Move to CLI_PENDING
8. **Wait for user approval**
9. If approved: Send connection request or apply

## Deduplication (85% Fuzzy Match)

```
Added: "TechCorp" + "Software Engineer"

Check "TechCorp" + "Engineer" → 90% match → DUPLICATE ❌
Check "Tech Corp" + "SE" → 75% match → ALLOWED ✅
Check "Other" + "Role" → 10% match → ALLOWED ✅
```

## Gmail Configuration

### Get App Password
1. https://myaccount.google.com/apppasswords
2. Select "Mail" + "Windows Computer"
3. Copy 16-character token
4. Set in `.env`: `GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx`

### Email Polling
- Interval: 30 seconds
- Method: IMAP UNSEEN flag
- OTP extraction: 2-minute window with regex

## LinkedIn Stealth Features

- User-Agent: Chrome on macOS 10.15
- Randomized delays: 2-8 seconds between actions
- Mouse movements before clicks
- Viewport height: 1080px
- Cookie persistence: `/tmp/linkedin_session/cookies.json`
- Rate limit: 20 minutes between runs

## Llama 3.1 Integration

- Model: `llama2:latest` or `llama3.1:8b`
- Context: 32K tokens
- Output: Structured JSON
- Use: Email responses, job analysis
- Local inference: No API keys needed

## Logging

```
logs/
├── orchestrator.log       # Main agent
├── gmail_mcp.log         # Email server
├── linkedin_mcp.log      # LinkedIn server
└── jobportal_mcp.log     # Job portal server

Rotation: 10MB per file (3 backups)
Format: {timestamp} | {level} | {name}:{function}:{line} | {message}
```

## Environment Variables

| Variable | Required | Example |
|----------|----------|---------|
| `GMAIL_ADDRESS` | Yes | `your@gmail.com` |
| `GMAIL_APP_PASSWORD` | Yes | `xxxx xxxx xxxx xxxx` |
| `LINKEDIN_EMAIL` | No | `your@gmail.com` |
| `LINKEDIN_PASSWORD` | No | `your-password` |
| `METADATA_FILE` | No | `~/.llm_agent/metadata.json` |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` |
| `OLLAMA_MODEL` | No | `llama2:latest` |

## File Permissions

```bash
~/.llm_agent/
├── metadata.json (600: rw-------)    ← Encrypted
├── salt (600: rw-------)             ← PBKDF2 salt
└── cookies.json (600: rw-------)     ← LinkedIn session

/tmp/linkedin_session/
└── cookies.json (600: rw-------)
```

## Performance Tips for M4

- Increase context: `ollama_context = 32000`
- Faster polling: `gmail_poll_interval = 15` (min 10s)
- Parallel processing: Possible with `asyncio.gather()`
- Browser pool: Could cache browser across jobs

## Troubleshooting Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed: `pip list | grep -E "loguru|playwright|pydantic"`
- [ ] Ollama running: `ollama serve` in another terminal
- [ ] Model downloaded: `ollama list | grep llama`
- [ ] Gmail app password set in `.env` (not account password)
- [ ] Metadata encrypted: `ls ~/.llm_agent/metadata.json`
- [ ] Logs viewable: `tail logs/orchestrator.log`

## Safety Checklist

- [ ] Store passwords in `.env` (not in code)
- [ ] Set file permissions to 600 for metadata
- [ ] Use separate Gmail account if possible
- [ ] Test with one job before batch mode
- [ ] Monitor first 24 hours of operation
- [ ] Respect LinkedIn rate limits (20 min min interval)

## Advanced Configurations

### Custom Email Prompt
Edit: `orchestrator/agent.py` → `_build_email_prompt()`

### Change LLM Model
Edit: `.env` → `OLLAMA_MODEL=llama3.1:8b`

### Adjust Deduplication
Edit: `config/models.py` → `dedup_similarity_threshold = 0.80` (80%)

### Parallel Job Processing
Edit: `orchestrator/agent.py` → Use `asyncio.gather()` for multiple jobs

## More Help

- Full docs: See `README.md`
- Issues: Check `logs/orchestrator.log`
- Source: Check `orchestrator/agent.py` comments
- Tests: Run `pytest tests/ -v`

---

**Last Updated**: March 2026 | **Version**: 1.0 | **Mac mini M4**
