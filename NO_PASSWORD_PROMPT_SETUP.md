# Running Agent Without Password Prompt

## What Changed

Previously, when you ran `python orchestrator/agent.py`, it would prompt you to enter the master password:
```
Enter master password: 
```

This required manual interaction and blocked automatic execution.

## New Behavior

The agent now **automatically loads the password from an environment variable** instead of prompting:

### ✅ How to Use

#### Option 1: Set Environment Variable Temporarily (Single Session)

```bash
# Set password in current terminal session
export ENCRYPTION_PASSWORD="your-encryption-password"

# Run the agent (no prompt!)
python orchestrator/agent.py
```

#### Option 2: Set in `.env` File (Automatic Loading)

The agent already loads from `.env` with `python-dotenv`. Add to your `.env` file:

```bash
# .env file
ENCRYPTION_PASSWORD="your-encryption-password"
```

Then just run:
```bash
python orchestrator/agent.py
```

The password is automatically loaded from `.env` 🎉

#### Option 3: Set Permanently in Shell Profile (Persistent)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Add this line to your shell profile
export ENCRYPTION_PASSWORD="your-encryption-password"
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### 🔐 Security Considerations

⚠️ **Important:**
- The password is now stored in environment variables
- For **local development:** `export` in terminal is fine
- For **production/servers:** Use proper secret management (AWS Secrets Manager, HashiCorp Vault, etc.)
- **Never** commit `.env` files with passwords to Git
- Use `.gitignore` to exclude `.env`:
  ```bash
  # .gitignore
  .env
  .env.local
  ```

### 📋 Setup Steps

1. **Find your encryption password** - it's the one you used to encrypt the metadata file

2. **Add to `.env`:**
   ```bash
   echo 'ENCRYPTION_PASSWORD="your-password"' >> .env
   ```

3. **Run the agent:**
   ```bash
   python orchestrator/agent.py
   ```

4. **Verify it works** - Look for log message:
   ```
   ✅ Metadata loaded successfully
   ```

### 🔍 What Happens

#### If ENCRYPTION_PASSWORD is set:
```
Agent starts
    ↓
Loads password from environment variable
    ↓
Decrypts and loads metadata
    ↓
✅ Ready to run
```

#### If ENCRYPTION_PASSWORD is NOT set:
```
Agent starts
    ↓
Looks for ENCRYPTION_PASSWORD
    ↓
Not found → Logs warning
    ↓
Skips metadata loading
    ↓
⚠️  Email replies disabled (but agent still runs!)
```

### ✅ Expected Log Output

With password set:
```
09:50:00 | INFO     | 🤖 JOB AUTOMATION ORCHESTRATOR STARTING
09:50:00 | INFO     | Agent start time: 2026-03-15T09:50:00.123456
09:50:00 | INFO     | Initializing MCP servers...
09:50:01 | INFO     | ✅ MCP servers initialized
09:50:01 | INFO     | Loading encrypted metadata...
09:50:01 | INFO     | ✅ Metadata loaded successfully  ← PASSWORD WAS FOUND
09:50:01 | INFO     | ✅ Orchestrator ready
```

Without password set:
```
09:50:00 | INFO     | 🤖 JOB AUTOMATION ORCHESTRATOR STARTING
09:50:00 | INFO     | Agent start time: 2026-03-15T09:50:00.123456
09:50:00 | INFO     | Initializing MCP servers...
09:50:01 | INFO     | ✅ MCP servers initialized
09:50:01 | INFO     | Loading encrypted metadata...
09:50:01 | WARNING  | ⚠️  ENCRYPTION_PASSWORD not set in environment
09:50:01 | WARNING  | To enable: export ENCRYPTION_PASSWORD='your-password'  ← NEEDS PASSWORD
09:50:01 | WARNING  | Metadata not loaded - email replies disabled (approval still works)
09:50:01 | INFO     | ✅ Orchestrator ready
```

### 🚀 Automated Startup Scripts

#### For Cron Jobs (Scheduled Automation)

Create a file `start_agent.sh`:

```bash
#!/bin/bash

# Source environment variables
export ENCRYPTION_PASSWORD="your-password"

# Start the agent
cd /path/to/job_automation_agent
source .venv/bin/activate
python orchestrator/agent.py
```

Make it executable:
```bash
chmod +x start_agent.sh
```

Run anytime:
```bash
./start_agent.sh
```

#### For Crontab (Automatic Scheduling)

Add to crontab:
```bash
# Run agent every hour
0 * * * * export ENCRYPTION_PASSWORD="your-password" && cd /path/to/job_automation_agent && source .venv/bin/activate && python orchestrator/agent.py
```

Or better (in a script):
```bash
crontab -e

# Add this line:
0 * * * * /path/to/start_agent.sh >> /var/log/job_automation.log 2>&1
```

### 💡 Environment Variable Priority

1. **Explicit export** (highest priority)
   ```bash
   export ENCRYPTION_PASSWORD="value"
   ```

2. **`.env` file** (loaded by python-dotenv)
   ```
   ENCRYPTION_PASSWORD=value
   ```

3. **Shell profile** (`~/.bashrc`, `~/.zshrc`)
   ```bash
   export ENCRYPTION_PASSWORD=value
   ```

4. **Not set** (lowest - agent skips metadata)

### 🔑 Getting Your Password

If you forgot the password, check:

1. **Git history** (if stored previously)
   ```bash
   git log -p --all -S "password" | head -50
   ```

2. **Shell history** (if you ran it before)
   ```bash
   history | grep "ENCRYPTION_PASSWORD"
   ```

3. **Password manager** (if saved there)

4. **Original setup notes** (from when you encrypted the file)

### 📝 Configuration Examples

#### Minimal Setup (.env only)
```bash
# .env
ENCRYPTION_PASSWORD="my-secret-password-123"
```

```bash
# Run (with no password prompt)
python orchestrator/agent.py
```

#### Docker/Container Setup
```dockerfile
FROM python:3.11

# Pass password at runtime
ENV ENCRYPTION_PASSWORD=${ENCRYPTION_PASSWORD}

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "orchestrator/agent.py"]
```

Run with:
```bash
docker run -e ENCRYPTION_PASSWORD="your-password" job-automation-agent
```

### ✨ Summary

| Method | Setup | Security | Effort |
|--------|-------|----------|--------|
| export | `export PASS="x"` | Low (visible in history) | ⭐ |
| .env | `PASS="x"` in file | Medium (file-based) | ⭐⭐ |
| Shell Profile | Add to `~/.bashrc` | Medium (persistent) | ⭐⭐ |
| Vault/Secrets | External service | High (encrypted) | ⭐⭐⭐⭐ |

### 🔧 Troubleshooting

**Q: Still getting password prompt?**
A: Ensure `ENCRYPTION_PASSWORD` is set in environment:
```bash
echo $ENCRYPTION_PASSWORD
# Should print your password, not empty
```

**Q: Password not being read?**
A: Check `.env` file exists and has correct line:
```bash
grep ENCRYPTION_PASSWORD .env
# Should show your password
```

**Q: "Metadata not loaded" warning?**
A: This is normal if you don't want email replies. Agent still runs fine!

**Q: How to verify metadata was loaded?**
A: Check logs for:
```bash
grep "Metadata loaded successfully" logs/orchestrator.log
```

---

**Status:** ✅ Setup Complete  
**Password Prompt:** Eliminated  
**Automation:** Ready for 24/7 operation!

