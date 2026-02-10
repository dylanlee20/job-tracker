# Session Recovery Guide

When Claude Code crashes or you get an API error, use this guide to quickly recover.

## Quick Recovery (Copy-Paste This)

When starting a new Claude session after a crash, just say:

```
Read CLAUDE.md and help me continue working on job-tracker.
Check git status to see what was in progress.
```

## What Happens Automatically

With the everything-claude-code setup, these things happen automatically:
- Session state is saved when you end a session
- Hooks remind you about uncommitted changes
- Rules ensure consistent coding standards

## Manual Recovery Steps

### Step 1: Check what was in progress
```bash
cd ~/Desktop/job-tracker
git status
git diff
git log --oneline -5
```

### Step 2: Check recent file changes
```bash
ls -lt scrapers/ | head -5    # Most recently modified scrapers
ls -lt | head -10             # Most recently modified files
```

### Step 3: Check for errors
```bash
cat data/logs/scraper.log | tail -50
```

### Step 4: Test if app runs
```bash
python app.py
```

## Best Practices to Prevent Data Loss

1. **Commit frequently** - After every meaningful change:
   ```
   /checkpoint
   ```
   Or just ask: "commit my current changes"

2. **Use /checkpoint** - Saves verification state so you can resume

3. **End sessions cleanly** - Say "let's wrap up" so hooks can save state

4. **Keep CLAUDE.md updated** - Add notes about current work:
   ```
   Update CLAUDE.md with what we're working on
   ```

## Recovery Commands Reference

| Situation | What to say |
|-----------|-------------|
| After API error | "Read CLAUDE.md and continue where we left off" |
| Forgot what we were doing | "Check git log and CLAUDE.md to see recent work" |
| Something broke | "/build-fix" |
| Want to save progress | "/checkpoint" or "commit these changes" |
| Review before committing | "/code-review" |

## Session History

Your previous sessions are stored at:
```
~/.claude/projects/-Users-jingtaoli/
```

You can search them:
```bash
grep "job-tracker" ~/.claude/projects/-Users-jingtaoli/*.jsonl
```
