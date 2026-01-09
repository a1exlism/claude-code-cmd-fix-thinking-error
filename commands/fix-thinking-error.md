---
description: Fix API Error 400 - Invalid signature in thinking block
allowed-tools: Bash(python3:*, ls:*, cp:*, pwd:*)
argument-hint: [--list] [--index <n>] [--list-backups] [--restore] [--delete] [--global]
---

# Fix Claude Code Thinking Block Error

Fix API Error 400 - Invalid signature in thinking block by removing corrupted thinking/redacted_thinking blocks from session files.

## Context

- Arguments: $ARGUMENTS
- Current working directory: use `pwd` to get it
- Session directory: `~/.claude/projects/`
- Fix script: `~/.claude/fix_claude_thinking_error.py`

## Execution

First, check if the fix script exists:

```bash
!`ls -la ~/.claude/fix_claude_thinking_error.py 2>/dev/null || echo "NOT_FOUND"`
```

If script not found, inform user to install from:
https://github.com/a1exlism/claude-code-cmd-fix-thinking-error

Then execute the fix script. By default, filter to current project only using `--cwd`:

```bash
python3 ~/.claude/fix_claude_thinking_error.py --cwd "$(pwd)" $ARGUMENTS
```

If user passes `--global` argument, run without `--cwd` to fix all projects:

```bash
python3 ~/.claude/fix_claude_thinking_error.py $ARGUMENTS
```

## Options

| Option | Description |
|--------|-------------|
| `--list` / `-l` | List all session files |
| `--file <path>` / `-f` | Fix specific file |
| `--index <n>` / `-i` | Fix/restore file by index |
| `--list-backups` / `-lb` | List all backup files |
| `--restore` / `-r` | Restore session from backup |
| `--delete` / `-d` | Delete backup after restore |
| `--cwd <path>` / `-c` | Filter sessions by project directory |
| `--global` | Fix all projects (not just current) |

> **Note**: `--all` and `--no-backup` are available but require manual confirmation. Not recommended for automated use.

## Post-fix Actions

**IMPORTANT**: After fixing, you MUST reload the session. The fix only modifies the file on disk, not the current session in memory.

Execute this command to reload:

```
/resume
```

Then select the current session to reload it with the fixed data.

> ⚠️ DO NOT continue using the current session after fixing. The error will persist until you `/resume`.

---

**Reference**: [Issue #10199](https://github.com/anthropics/claude-code/issues/10199)
