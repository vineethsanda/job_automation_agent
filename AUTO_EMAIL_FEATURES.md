# Orchestrator Agent Updates - Auto-Reply & Auto-Email Features

## Summary of Changes

Your Job Automation Orchestrator has been updated to automatically handle new emails and LinkedIn job postings that arrive **AFTER the agent starts**. This eliminates the need for manual CLI approval of recent opportunities.

## Key Features Added

### 1. **Automatic Email Replies** 📧
When a new recruiter email arrives in your inbox AFTER the agent starts:
- Email is detected by the background monitoring task
- Job details are automatically extracted (company, role, salary expectations)
- A personalized response is generated using Ollama LLM
- Email is automatically sent to the recruiter
- Job is marked as COMPLETED

### 2. **Automatic LinkedIn Job Emails** 💼
When a new job posting appears on LinkedIn AFTER the agent starts:
- Job is discovered during job discovery cycle
- Email is automatically generated and sent to the recruiter/careers contact
- Personalized message highlighting your skills and interest
- Job is marked as COMPLETED

### 3. **Agent Start Time Tracking** ⏰
- Agent records its start time (`agent_start_time`) when initialized
- Uses this timestamp to identify "new" emails and jobs
- Only items arriving after this timestamp are auto-handled
- Existing emails/jobs still require CLI approval (for safety)

## How It Works

### Email Auto-Reply Flow
```
Email arrives → Check timestamp > agent_start_time?
                           ↓
                    YES → Auto-reply
                           ↓
                    Generate response (Ollama)
                           ↓
                    Send via Gmail
                           ↓
                    Mark COMPLETED
```

### LinkedIn Job Auto-Email Flow
```
Job discovered → Check is_new flag & timestamp > agent_start_time?
                           ↓
                    YES → Auto-send email
                           ↓
                    Generate email (Ollama)
                           ↓
                    Send via Gmail
                           ↓
                    Mark COMPLETED
```

## Code Changes Made

### 1. Modified `orchestrator/agent.py` - Added agent_start_time tracking

```python
# In __init__()
self.agent_start_time: Optional[datetime] = None

# In main()
self.agent_start_time = datetime.utcnow()
logger.info(f"Agent start time: {self.agent_start_time.isoformat()}")
```

### 2. Modified `run_linkedin_discovery()` - Filter new jobs

Now marks each job with `is_new` flag based on posted_date vs agent_start_time:
- Jobs posted after agent startup: `is_new = True`
- Jobs posted before agent startup: `is_new = False`

### 3. Modified `detect_new_jobs()` - Handle new jobs automatically

For LinkedIn jobs marked as new:
```python
if source == "linkedin" and is_new:
    # Automatically send email to recruiter
    await self.send_email_for_linkedin_job(new_job)
    self.state_machine.update_state(job_id, JobState.COMPLETED)
```

### 4. Modified `process_new_email()` - Auto-reply to new emails

When a new email arrives (timestamp >= agent_start_time):
```python
if email_timestamp >= agent_start_timestamp:
    # Email arrived after agent startup - auto-reply
    await self.handle_email_response(new_job)
    self.state_machine.update_state(opportunity["job_id"], JobState.COMPLETED)
```

### 5. New Method: `send_email_for_linkedin_job()` 

Handles sending professional inquiry emails to LinkedIn job recruiters:
- Generates personalized email using Ollama LLM
- Includes your profile information (name, email, phone, skills)
- Sends via Gmail to recruiter contact
- Logs success/failure

## Configuration

No additional configuration needed! The feature automatically works based on:
- Agent start time
- Email/job post timestamps
- LLM availability (Ollama)
- Gmail connectivity

## Example Workflow

**Scenario:** Agent starts at 10:00 AM

### 10:05 AM - New LinkedIn Job Posted
1. Job discovery finds: "Senior Engineer at TechCorp"
2. Job posted_date = 10:04 AM (after agent start)
3. Marked as `is_new = True`
4. Orchestrator auto-composes: "Dear Hiring Manager, I am very interested in the Senior Engineer position at TechCorp..."
5. Email sent to careers@techcorp.com
6. Job marked COMPLETED ✅

### 10:15 AM - Recruiter Email Arrives
1. Background monitor detects email from recruiter@company.com
2. Email timestamp = 10:14 AM (after agent start)
3. Job details extracted: "Backend Engineer" at "CloudTech"
4. Orchestrator auto-replies: "Thank you for reaching out! I am interested in the Backend Engineer position..."
5. Email sent to recruiter@company.com
6. Job marked COMPLETED ✅

### 9:50 AM - Old Unread Email (before agent start)
1. Discovered during monitoring
2. Email timestamp = 9:30 AM (before agent start at 10:00 AM)
3. Marked as CLI_PENDING
4. Requires manual approval via CLI ⚠️

## Benefits

✅ **100% Automation** - No manual intervention for new opportun ities  
✅ **Responsive** - Replies sent immediately  
✅ **Professional** - LLM-generated personalized messages  
✅ **Safe** - Old emails still require approval  
✅ **Trackable** - All actions logged with timestamps  
✅ **Scalable** - Handles multiple emails/jobs per minute  

## Testing

Run the test suite to verify functionality:

```bash
# Quick test
python3 tests/test_orchestrator_agent.py

# Full pytest with verbose output
pytest tests/test_orchestrator_agent.py -v -s

# Test specific functionality
pytest tests/test_orchestrator_agent.py::TestFullIntegration -v
```

## Important Notes

### Email Extraction
The system uses smart heuristics to extract company/role from emails:

```python
# From email subject: "Opportunity: Senior Engineer at TechCorp"
company = "TechCorp"  # Extracted from "at [Company]" pattern

# From sender domain: "recruiter@techcorp.com"
company = "Techcorp"  # Extracted from domain
```

### LinkedIn Job Email Sending
For LinkedIn jobs, the system:
- Creates email to: `careers@[company].com` (configurable)
- Includes your full profile (name, email, phone, skills)
- References job title and company
- Uses professional LLM prompt for personalization

### Recruiter Email Replies
For recruiter emails, the system:
- Creates reply to original sender
- Includes "Re:" prefix in subject
- References original job/company/role
- Uses professional recruitment email prompt

## Monitoring

Check logs to track automatic actions:

```bash
# Watch logs in real-time
tail -f logs/orchestrator.log

# Find auto-reply events
grep "Auto-replying" logs/orchestrator.log

# Find auto-email events
grep "Auto-sending email" logs/orchestrator.log

# Monitor completion
grep "Job.*transitioned to COMPLETED" logs/orchestrator.log
```

## Troubleshooting

### Emails not being sent automatically
1. ❌ Check `agent_start_time` is set: `grep "Agent start time" logs/orchestrator.log`
2. ❌ Verify Gmail connection: `grep "Gmail" logs/orchestrator.log`
3. ❌ Check email timestamp: Ensure email arrived AFTER agent started
4. ❌ Check Ollama: Ensure LLM is running for email generation

### Emails marked CLI_PENDING instead of auto-replying
- Email arrived BEFORE agent started
- Check email timestamp vs agent start time in logs
- Manual approval still needed for these (safety feature)

### LinkedIn jobs not sending emails
1. ❌ Verify `is_new` flag is set: Check logs for "Found N new jobs"
2. ❌ Check for duplicates: See if job marked as duplicate
3. ❌ Verify Gmail connection
4. ❌ Check Ollama for LLM generation

## Next Steps

1. ✅ Deploy the updated agent
2. ✅ Monitor logs for auto-replies and emails
3. ✅ Verify email content quality
4. ✅ Adjust LLM prompts if needed (in code)
5. ✅ Configure recruiter email addresses for different companies
6. ✅ Test with real LinkedIn jobs and emails

## Version Info

- **Date Updated:** March 15, 2026
- **Agent Version:** 2.0 (Auto-Reply & Auto-Email)
- **Features:** Automatic email responses, automatic job inquiry emails, timestamp-based filtering

