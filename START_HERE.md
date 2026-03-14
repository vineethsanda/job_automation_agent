# 🚀 IMMEDIATE START GUIDE

**Complete job automation agent in 5 minutes**

```bash
# STEP 1: Initial Setup (run once)
cd ~/Desktop/llm
./setup.sh

# STEP 2: Get Gmail App Password
# Go to: https://myaccount.google.com/apppasswords
# Select "Mail" and "Windows Computer"
# Copy the 16-character token

# STEP 3: Configure
nano .env
# Set: GMAIL_ADDRESS=your@gmail.com
# Set: GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# STEP 4: Create Metadata
python3 setup_metadata.py
# Follow prompts - create master password here

# STEP 5: Start Ollama (Terminal 1)
ollama serve
# Or: brew install ollama && ollama serve

# STEP 6: Start Agent (Terminal 2)
cd ~/Desktop/llm
source venv/bin/activate
./start_agent.sh orchestrator

# When prompted, enter your master password

# STEP 7: Approve Jobs
# The agent will show jobs in your terminal
# Press [y] to approve, [n] to reject, [v] to view details
```

## What Happens Next

1. **Gmail monitoring** (every 30s): Agent checks for recruiter emails
2. **LinkedIn discovery** (every 20min): Agent scrapes job listings with stealth
3. **Deduplication**: Fuzzy matching prevents duplicate applications
4. **CLI approval**: You approve/reject each job in the terminal
5. **Processing**: Approved jobs get personalized email replies or applications
6. **Logging**: Everything logged to `logs/orchestrator.log`

## Key Files

| File | Purpose |
|------|---------|
| `.env` | Environment vars (Gmail, LinkedIn credentials) |
| `~/.llm_agent/metadata.json` | Your encrypted personal info |
| `logs/orchestrator.log` | Agent activity log |
| `/tmp/linkedin_session/` | LinkedIn cookies (temporary) |

## Troubleshooting

If agent won't start:
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check environment
cat .env | grep GMAIL

# Check metadata
ls -la ~/.llm_agent/metadata.json

# View logs
tail -f logs/orchestrator.log

# Test manually
python3 -c "from utils.encryption import ConfigEncryption; print('✅ Imports OK')"
```

## Stopping the Agent

```bash
# Press Ctrl+C in terminal running orchestrator
# Logs saved to: logs/orchestrator.log
```

## Next: Full Documentation

- **Full setup guide**: See [README.md](README.md)
- **Complete code reference**: See [DELIVERY_SUMMARY.md](DELIVERY_SUMMARY.md)
- **Quick command reference**: See [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

**Ready to go?** 
Run `./setup.sh` then `./start_agent.sh orchestrator` 🎉
