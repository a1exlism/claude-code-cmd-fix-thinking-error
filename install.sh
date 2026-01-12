#!/bin/bash
# Claude Code Thinking Block Fix - Installation Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
COMMANDS_DIR="$CLAUDE_DIR/commands"
HOOKS_EXAMPLE="$SCRIPT_DIR/hooks/hooks-example.json"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

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
read -r -p "Install Claude Code hooks config (SessionStart check)? [y/N]: " install_hooks
if [[ "$install_hooks" == "y" || "$install_hooks" == "Y" ]]; then
    if [[ ! -f "$HOOKS_EXAMPLE" ]]; then
        echo "Warning: hooks example not found: $HOOKS_EXAMPLE"
    elif [[ ! -f "$SETTINGS_FILE" ]]; then
        cp "$HOOKS_EXAMPLE" "$SETTINGS_FILE"
        echo "✅ Installed: ~/.claude/settings.json"
    else
        backup_path="$SETTINGS_FILE.bak.$(date +%Y%m%d_%H%M%S)"
        cp "$SETTINGS_FILE" "$backup_path"
        echo "Backup created: $backup_path"
        if python3 - "$SETTINGS_FILE" "$HOOKS_EXAMPLE" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
example_path = Path(sys.argv[2])

try:
    existing = json.loads(settings_path.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    print(f"Invalid JSON in {settings_path}: {exc}", file=sys.stderr)
    sys.exit(1)

example = json.loads(example_path.read_text(encoding="utf-8"))

if not isinstance(existing, dict) or not isinstance(example, dict):
    print("Settings and example configs must be JSON objects.", file=sys.stderr)
    sys.exit(1)

hooks = existing.get("hooks")
if hooks is None:
    hooks = {}
if not isinstance(hooks, dict):
    print("Existing hooks config must be a JSON object.", file=sys.stderr)
    sys.exit(1)

example_hooks = example.get("hooks", {})
if not isinstance(example_hooks, dict):
    print("Example hooks config must be a JSON object.", file=sys.stderr)
    sys.exit(1)

updated = False
for event, hook_list in example_hooks.items():
    if not isinstance(hook_list, list):
        print(f"Example hooks for {event} must be a list.", file=sys.stderr)
        sys.exit(1)
    current_list = hooks.get(event, [])
    if current_list is None:
        current_list = []
    if not isinstance(current_list, list):
        print(f"Existing hooks for {event} must be a list.", file=sys.stderr)
        sys.exit(1)
    for hook in hook_list:
        if hook not in current_list:
            current_list.append(hook)
            updated = True
    hooks[event] = current_list

if not updated and "hooks" in existing:
    sys.exit(0)

existing["hooks"] = hooks
settings_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
PY
        then
            echo "✅ Updated: ~/.claude/settings.json"
        else
            echo "Warning: failed to update settings.json. You can merge hooks manually from:"
            echo "   $HOOKS_EXAMPLE"
        fi
    fi
fi

echo ""
echo "Installation complete!"
echo ""
echo "Usage:"
echo "  /fix-thinking-error           # Fix latest session (via Claude Code)"
echo "  python3 ~/.claude/fix_claude_thinking_error.py  # Direct execution"
echo ""
echo "For more options, run: python3 ~/.claude/fix_claude_thinking_error.py --help"
