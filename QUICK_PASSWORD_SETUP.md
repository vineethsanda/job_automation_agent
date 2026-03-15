# ⚡ Quick Setup: No Password Prompt

## 🚀 Get Started in 30 Seconds

### Option 1: Use `.env` File (Recommended)

```bash
# 1. Edit .env file (or create if doesn't exist)
echo 'ENCRYPTION_PASSWORD="your-actual-encryption-password"' >> .env

# 2. Run agent (no prompt!)
python orchestrator/agent.py
```

### Option 2: Export in Terminal

```bash
# 1. Set password for this session only
export ENCRYPTION_PASSWORD="your-actual-encryption-password"

# 2. Run agent (no prompt!)
python orchestrator/agent.py
```

### Option 3: Skip Metadata (Minimal Setup)

If you don't have encrypted metadata or want to skip it:

```bash
# Just run agent (will skip metadata loading)
python orchestrator/agent.py
```

---

## ✅ What's Different Now

| Before | After |
|--------|-------|
| `Enter master password: _` (blocks) | No prompt! Starts automatically |
| Manual key entry required | Password from env variable |
| Can't use in cron/automation | Ready for 24/7 automation |

---

## 🔐 Setting Your Password

### Where to Find Your Password?

If you encrypted your metadata file before, you used a password. You need that same password.

**Check these locations:**
1. Your password manager
2. Git commit history: `git log -p | grep password`
3. Shell history: `history | grep ENCRYPTION`
4. Original setup notes/files

---

## 📝 Complete Setup Steps

### Step 1: Locate Your Password
Find the encryption password you used before (the one that encrypted your metadata file)

### Step 2: Add to `.env`
```bash
# Open the .env file in your project root
# Add or update this line:
ENCRYPTION_PASSWORD="your-actual-password-here"

# Example:
ENCRYPTION_PASSWORD="MySecure#Password123!"
```

### Step 3: Run Agent
```bash
# First time - may need to activate venv
source .venv/bin/activate

# Run the agent
python orchestrator/agent.py
```

### Step 4: Verify
You should see in logs:
```
✅ Metadata loaded successfully
✅ Orchestrator ready
```

---

## ✨ Benefits

✅ **No manual input** - Runs automatically  
✅ **24/7 automation** - Can use in cron/systemd  
✅ **Cleaner logs** - No interactive prompts  
✅ **Better security** - Uses environment variables not shell history  

---

## 🧪 Test It

```bash
# Verify password is set
echo $ENCRYPTION_PASSWORD

# Should print your password, not empty!
# If empty, set it:
export ENCRYPTION_PASSWORD="your-password"

# Then run agent
python orchestrator/agent.py
```

---

## 📖 Full Documentation

For detailed information, see: **NO_PASSWORD_PROMPT_SETUP.md**

---

## 💡 Common Issues

**Q: Still asking for password?**
```bash
# Verify environment variable is set
echo $ENCRYPTION_PASSWORD
# If empty, run:
export ENCRYPTION_PASSWORD="your-password"
```

**Q: What if I don't have the password?**
- Agent will skip metadata loading
- Email replies feature will be disabled
- But the rest of the agent will still work!

**Q: Can I run without metadata?**
```bash
# Yes! Just don't set ENCRYPTION_PASSWORD
# Agent will log a warning but continue
python orchestrator/agent.py
```

---

## 🎯 Next Steps

1. Add `ENCRYPTION_PASSWORD` to `.env`
2. Run `python orchestrator/agent.py`
3. Monitor logs: `tail -f logs/orchestrator.log`
4. Enjoy hands-free automation! 🎉

---

**Status:** ✅ Ready to Deploy  
**Password Prompt:** Eliminated  
**Setup Time:** < 1 minute
