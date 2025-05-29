# Claude Code Project Setup Guide

This guide outlines the procedure to follow when starting Claude Code with any project, using the EconCell project as an example.

## Initial Setup Procedure

### 1. Initial Project Assessment
When first opening a project with Claude Code, it should:
- Read CLAUDE.md to understand project-specific instructions
- Review pyproject.toml/package.json to understand dependencies
- Check directory structure to map out the codebase
- Examine git status to see current work state

### 2. Environment Verification
Verify the development environment is properly configured:

```bash
# Check Python/Node version matches project requirements
python --version
pip --version

# Verify key tools are available
which scrapy  # or other project-specific tools
psql --version  # if using PostgreSQL
```

### 3. Understand Recent Context
Review the project's recent history and current state:

```bash
# Review recent commits
git log --oneline -10

# Check current branch
git branch --show-current

# See what's changed
git status
```

### 4. Test Key Commands
Run a few commands from CLAUDE.md to ensure the environment works:

```bash
# For EconCell project:
python src/scheduler/start_scheduler.py status
cd src/econdata && scrapy list
```

### 5. Create Working Memory
Use TodoWrite to track any immediate tasks or issues found during setup.

## Quick Reference Card for EconCell

Most common commands you'll use:

```bash
# Run scrapers
cd src/econdata
scrapy crawl rba_tables
scrapy crawl xrapi-currencies

# Scheduler management
python src/scheduler/start_scheduler.py start/stop/status

# API server
uvicorn site.api:app --reload

# Code quality
black --line-length 100 src/
pytest -v --tb=short

# AI testing
python test_ai_system.py
```

## Setup Checklist Template

When starting Claude Code on any project:

1. ✓ CLAUDE.md exists and is read
2. ✓ Project dependencies understood (pyproject.toml/package.json)
3. ✓ Git status checked for uncommitted changes
4. ✓ Development environment verified
5. ✓ Key commands tested
6. ✓ Todo list initialized for session tasks

## Benefits of This Approach

This systematic approach ensures:
- You understand the project context before making changes
- The development environment is verified to work correctly
- You have a clear starting point for any tasks
- Project-specific conventions and commands are understood
- Any setup issues are identified early

## Notes

- Always check CLAUDE.md first as it contains project-specific guidance
- Use the TodoWrite tool frequently to track tasks and give visibility to progress
- Test commands before assuming they work
- Review recent commits to understand current development focus