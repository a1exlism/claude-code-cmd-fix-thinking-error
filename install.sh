#!/bin/bash
# Claude Code Thinking Block Fix - Installation Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
COMMANDS_DIR="$CLAUDE_DIR/commands"

echo "Installing Claude Code Thinking Block Fix..."
echo ""

# Create directories if needed
mkdir -p "$CLAUDE_DIR"
mkdir -p "$COMMANDS_DIR"

# Copy main script
cp "$SCRIPT_DIR/fix_claude_thinking_error.py" "$CLAUDE_DIR/"
echo "✅ Installed: ~/.claude/fix_claude_thinking_error.py"

# Copy command file
cp "$SCRIPT_DIR/commands/fix-thinking-error.md" "$COMMANDS_DIR/"
echo "✅ Installed: ~/.claude/commands/fix-thinking-error.md"

echo ""
echo "Installation complete!"
echo ""
echo "Usage:"
echo "  /fix-thinking-error           # Fix latest session (via Claude Code)"
echo "  python3 ~/.claude/fix_claude_thinking_error.py  # Direct execution"
echo ""
echo "For more options, run: python3 ~/.claude/fix_claude_thinking_error.py --help"
