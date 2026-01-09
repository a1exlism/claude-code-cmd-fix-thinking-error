# Claude Code Thinking Block Fix

Fix for Claude Code API Error 400 - Invalid signature in thinking block.

## Problem

When using Claude Code with extended thinking mode, you may encounter this error:

```
API Error: 400 {"type":"error","error":{"type":"invalid_request_error","message":"messages.X.content.0: Invalid `signature` in `thinking`block"}}
```

This happens when thinking blocks in session files become corrupted.

## Solution

This tool removes corrupted `thinking` and `redacted_thinking` blocks from Claude Code session files, allowing you to resume your conversation.

## Installation

### Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/a1exlism/claude-code-cmd-fix-thinking-error.git
cd claude-code-cmd-fix-thinking-error

# Run install script
./install.sh
```

### Manual Install

```bash
# Copy the fix script
cp fix_claude_thinking_error.py ~/.claude/

# Copy the command file (optional, for /fix-thinking-error command)
mkdir -p ~/.claude/commands
cp commands/fix-thinking-error.md ~/.claude/commands/
```

## Usage

> **Recommended**: Run the script directly in an external terminal (not inside Claude Code) to avoid generating new thinking blocks during the fix process.

### Method 1: Direct Python Script (Recommended)

```bash
# Fix latest session (default)
python3 ~/.claude/fix_claude_thinking_error.py

# List all session files
python3 ~/.claude/fix_claude_thinking_error.py --list

# Fix all session files
python3 ~/.claude/fix_claude_thinking_error.py --all

# Fix specific file
python3 ~/.claude/fix_claude_thinking_error.py --file /path/to/session.jsonl

# Fix by index (from --list)
python3 ~/.claude/fix_claude_thinking_error.py --index 2

# Skip backup (use with caution)
python3 ~/.claude/fix_claude_thinking_error.py --no-backup
```

### Method 2: Claude Code Command (after installation)

```bash
/fix-thinking-error           # Fix latest session (default)
/fix-thinking-error --list    # List all session files
/fix-thinking-error --all     # Fix all session files
```

> Note: Using `/fix-thinking-error` inside Claude Code may generate new thinking blocks. If the error persists after fixing, run the script again from an external terminal.

## Options

| Option                   | Description                             |
| ------------------------ | --------------------------------------- |
| `--list` / `-l`          | List all session files                  |
| `--file <path>` / `-f`   | Fix specific file                       |
| `--index <n>` / `-i`     | Fix/restore file by index               |
| `--all` / `-a`           | Fix all session files                   |
| `--no-backup`            | Skip backup creation (use with caution) |
| `--cwd <path>` / `-c`    | Filter sessions by project directory    |
| `--list-backups` / `-lb` | List all backup files                   |
| `--restore` / `-r`       | Restore session from backup             |
| `--delete` / `-d`        | Delete backup after restore             |

## Filter by Project

When running multiple Claude Code instances, use `--cwd` to filter sessions by project:

```bash
# Fix only current project's sessions
python3 ~/.claude/fix_claude_thinking_error.py --cwd .

# List sessions for a specific project
python3 ~/.claude/fix_claude_thinking_error.py --cwd /path/to/project --list

# Fix all sessions (all projects)
python3 ~/.claude/fix_claude_thinking_error.py
```

> The `/fix-thinking-error` command automatically uses `--cwd` to filter to the current project. Use `--global` to fix all projects.

## Backup & Restore

### List Backups

```bash
python3 ~/.claude/fix_claude_thinking_error.py --list-backups
```

### Restore from Backup

```bash
# Restore latest backup
python3 ~/.claude/fix_claude_thinking_error.py --restore

# Restore specific backup by index
python3 ~/.claude/fix_claude_thinking_error.py --restore --index 2

# Restore and delete backup file
python3 ~/.claude/fix_claude_thinking_error.py --restore --delete
```

## After Fixing

Use `/resume` to reload the fixed session (**no restart required**):

```bash
# In Claude Code, reload the fixed session
/resume <session-name>

# Or from command line
claude --resume <session-name>
```

> **Note**: `/resume` re-reads the session file from disk, so you don't need to restart Claude Code. Just switch to another session and back, or use `/resume` to reload.

## How It Works

1. Locates Claude Code session files in `~/.claude/projects/`
2. Creates a timestamped backup (e.g., `session.jsonl.bak.20250109_120000`)
3. Removes `thinking` and `redacted_thinking` content blocks from messages
4. Writes the cleaned session file

## File Structure

```
claude-thinking-fix/
├── README.md                           # This file
├── install.sh                          # Installation script
├── fix_claude_thinking_error.py        # Main fix script
└── commands/
    └── fix-thinking-error.md           # Claude Code command file
```

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Linux    | ✅ Supported | Native support |
| macOS    | ✅ Supported | Native support |
| WSL      | ✅ Supported | Recommended for Windows users |
| Windows  | ❌ Not tested | Contributions welcome |

## Reference

- [Issue #10199 - BUG: API Error 400 - Thinking Block Modification Error](https://github.com/anthropics/claude-code/issues/10199)

## License

MIT License
