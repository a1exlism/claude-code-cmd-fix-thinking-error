#!/usr/bin/env python3
"""
Claude Code Thinking Block Error Fix Tool

Fixes API Error 400 - Invalid signature in thinking block
by removing corrupted thinking blocks from session files.

Usage:
  python fix_claude_thinking_error.py           # Fix latest session file
  python fix_claude_thinking_error.py --list    # List all session files
  python fix_claude_thinking_error.py --file <path>  # Fix specific file
  python fix_claude_thinking_error.py --all     # Fix all session files

Reference: https://github.com/anthropics/claude-code/issues/10199
"""

import json
import os
import sys
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import argparse


_REMOVED = object()


def get_claude_projects_dir():
    return Path.home() / ".claude" / "projects"


def path_to_project_dir(cwd):
    """Convert a path to Claude Code's project directory name format.

    Claude Code encodes paths by replacing both '/' and '_' with '-'.
    Example: /home/user/my_project -> -home-user-my-project
    """
    cwd = Path(cwd).resolve()
    # Claude Code replaces both '/' and '_' with '-'
    encoded = str(cwd).replace("/", "-").replace("_", "-")
    if encoded.startswith("-"):
        encoded = encoded[1:]
    return "-" + encoded if not encoded.startswith("-") else encoded


MIN_SESSION_SIZE = 20 * 1024  # 20KB - skip small session files (e.g., newly created after /clear)


def find_session_files(projects_dir, cwd=None, min_size=MIN_SESSION_SIZE, include_subagents=False):
    session_files = []

    if not projects_dir.exists():
        return session_files

    if cwd:
        project_dir_name = path_to_project_dir(cwd)
        search_dir = projects_dir / project_dir_name
        if not search_dir.exists():
            return session_files
        search_pattern = search_dir
    else:
        search_pattern = projects_dir

    for jsonl_file in search_pattern.rglob("*.jsonl"):
        try:
            # Skip subagent files unless explicitly included
            if not include_subagents and "/subagents/" in str(jsonl_file):
                continue
            stat = jsonl_file.stat()
            if min_size > 0 and stat.st_size < min_size:
                continue
            session_files.append({
                "path": jsonl_file,
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "mtime_str": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        except (OSError, PermissionError):
            continue

    session_files.sort(key=lambda x: x["mtime"], reverse=True)
    return session_files


def remove_thinking_blocks(obj):
    """
    Recursively remove thinking blocks from any data structure.
    Returns (cleaned_obj, removed_count)
    """
    removed = 0

    if isinstance(obj, dict):
        # Check if this dict is a thinking block itself
        if obj.get('type') in ('thinking', 'redacted_thinking'):
            return _REMOVED, 1

        # Recursively process all values
        new_dict = {}
        for key, value in obj.items():
            cleaned, count = remove_thinking_blocks(value)
            removed += count
            if cleaned is _REMOVED:
                continue
            new_dict[key] = cleaned
        return new_dict, removed

    elif isinstance(obj, list):
        new_list = []
        for item in obj:
            cleaned, count = remove_thinking_blocks(item)
            removed += count
            if cleaned is _REMOVED:
                continue
            new_list.append(cleaned)
        return new_list, removed

    else:
        return obj, 0


def fix_session_file(filepath, create_backup=True):
    """Fix a single session file by removing thinking blocks"""
    filepath = Path(filepath)

    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return False

    temp_path = None
    thinking_blocks_removed = 0
    lines_processed = 0

    try:
        if create_backup:
            try:
                backup_path = filepath.with_suffix(f".jsonl.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                shutil.copy2(filepath, backup_path)
                print(f"📦 Backup created: {backup_path}")
            except Exception as e:
                print(f"⚠️  Backup failed: {e}")

        with open(filepath, 'r', encoding='utf-8') as f_in, tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=filepath.parent, delete=False) as f_out:
            temp_path = Path(f_out.name)
            for line in f_in:
                line_stripped = line.rstrip()
                if not line_stripped or line_stripped.isspace():
                    continue

                lines_processed += 1
                try:
                    data = json.loads(line_stripped)

                    cleaned_data, removed = remove_thinking_blocks(data)
                    thinking_blocks_removed += removed

                    if cleaned_data is _REMOVED:
                        continue
                    f_out.write(json.dumps(cleaned_data, ensure_ascii=False) + '\n')
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON parse warning (line {lines_processed}): {e}")
                    f_out.write(line_stripped + '\n')
            f_out.flush()
            os.fsync(f_out.fileno())

        os.replace(temp_path, filepath)

        print(f"✅ Fixed: {filepath}")
        print(f"   Lines processed: {lines_processed}")
        print(f"   Thinking blocks removed: {thinking_blocks_removed}")
        return True

    except Exception as e:
        print(f"❌ Fix failed: {e}")
        return False
    finally:
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


def find_backup_files(projects_dir, cwd=None):
    backup_files = []

    if not projects_dir.exists():
        return backup_files

    if cwd:
        project_dir_name = path_to_project_dir(cwd)
        search_dir = projects_dir / project_dir_name
        if not search_dir.exists():
            return backup_files
        search_pattern = search_dir
    else:
        search_pattern = projects_dir

    for bak_file in search_pattern.rglob("*.jsonl.bak.*"):
        try:
            stat = bak_file.stat()
            original_name = bak_file.name.split('.bak.')[0] + '.jsonl'
            original_path = bak_file.parent / original_name
            backup_files.append({
                "path": bak_file,
                "original_path": original_path,
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "mtime_str": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        except (OSError, PermissionError):
            continue

    backup_files.sort(key=lambda x: x["mtime"], reverse=True)
    return backup_files


def list_backups(backup_files):
    """List all backup files"""
    if not backup_files:
        print("No backup files found")
        return

    print(f"\nFound {len(backup_files)} backup file(s):\n")
    print(f"{'#':<4} {'Size':>10} {'Created':<20} Path")
    print("-" * 100)

    for i, f in enumerate(backup_files, 1):
        size_str = f"{f['size'] / 1024:.1f} KB" if f['size'] < 1024*1024 else f"{f['size'] / 1024/1024:.1f} MB"
        rel_path = str(f['path']).replace(str(get_claude_projects_dir()), "~/.claude/projects")
        print(f"{i:<4} {size_str:>10} {f['mtime_str']:<20} {rel_path}")


def restore_backup(backup_path, delete_backup=False):
    """Restore a session file from backup"""
    backup_path = Path(backup_path)

    if not backup_path.exists():
        print(f"❌ Backup file not found: {backup_path}")
        return False

    # Determine original file path
    original_name = backup_path.name.split('.bak.')[0] + '.jsonl'
    original_path = backup_path.parent / original_name

    try:
        shutil.copy2(backup_path, original_path)
        print(f"✅ Restored: {original_path}")
        print(f"   From backup: {backup_path}")

        if delete_backup:
            backup_path.unlink()
            print(f"🗑️  Backup deleted: {backup_path}")

        return True
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False


def list_sessions(session_files):
    """List all session files"""
    if not session_files:
        print("No session files found")
        return

    print(f"\nFound {len(session_files)} session file(s):\n")
    print(f"{'#':<4} {'Size':>10} {'Modified':<20} Path")
    print("-" * 80)

    for i, f in enumerate(session_files, 1):
        size_str = f"{f['size'] / 1024:.1f} KB" if f['size'] < 1024*1024 else f"{f['size'] / 1024/1024:.1f} MB"
        # Mark small files that would be skipped
        skip_mark = " (skipped)" if f['size'] < MIN_SESSION_SIZE else ""
        # Simplify path display
        rel_path = str(f['path']).replace(str(get_claude_projects_dir()), "~/.claude/projects")
        print(f"{i:<4} {size_str:>10} {f['mtime_str']:<20} {rel_path}{skip_mark}")


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code Thinking Block Error Fix Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s              # Fix latest session file
  %(prog)s --cwd .      # Fix latest session for current project only
  %(prog)s --list       # List all session files
  %(prog)s --file /path/to/session.jsonl  # Fix specific file
  %(prog)s --all        # Fix all session files
  %(prog)s --no-backup  # Fix without creating backup

  %(prog)s --list-backups          # List all backup files
  %(prog)s --restore               # Restore latest backup
  %(prog)s --restore --index 2     # Restore backup by index
  %(prog)s --restore --delete      # Restore and delete backup
        """
    )
    parser.add_argument("--list", "-l", action="store_true", help="List all session files")
    parser.add_argument("--file", "-f", type=str, help="Specify file path to fix")
    parser.add_argument("--all", "-a", action="store_true", help="Fix all session files")
    parser.add_argument("--no-backup", action="store_true", help="Don't create backup files")
    parser.add_argument("--index", "-i", type=int, help="Fix/restore file by index (use with --list or --list-backups)")
    parser.add_argument("--cwd", "-c", type=str, help="Filter sessions by project directory (use '.' for current directory)")

    parser.add_argument("--list-backups", "-lb", action="store_true", help="List all backup files")
    parser.add_argument("--restore", "-r", action="store_true", help="Restore session from backup")
    parser.add_argument("--delete", "-d", action="store_true", help="Delete backup after restore (use with --restore)")

    args = parser.parse_args()

    cwd = None
    if args.cwd:
        cwd = Path(args.cwd).resolve() if args.cwd != "." else Path.cwd()
        print(f"📂 Project filter: {cwd}")

    projects_dir = get_claude_projects_dir()
    print(f"📁 Claude projects directory: {projects_dir}\n")

    if not projects_dir.exists():
        print(f"❌ Directory not found: {projects_dir}")
        sys.exit(1)

    if args.list_backups:
        backup_files = find_backup_files(projects_dir, cwd)
        list_backups(backup_files)
        return

    if args.restore:
        backup_files = find_backup_files(projects_dir, cwd)
        if not backup_files:
            print("❌ No backup files found")
            sys.exit(1)

        if args.index is not None:
            if args.index < 1 or args.index > len(backup_files):
                print(f"❌ Invalid index: {args.index} (valid range: 1-{len(backup_files)})")
                sys.exit(1)
            restore_backup(backup_files[args.index - 1]["path"], delete_backup=args.delete)
        else:
            print("🔄 Restoring latest backup:")
            print(f"   Backup: {backup_files[0]['path']}")
            print(f"   Created: {backup_files[0]['mtime_str']}\n")
            restore_backup(backup_files[0]["path"], delete_backup=args.delete)
        return

    session_files = find_session_files(projects_dir, cwd)

    if args.list:
        # Show all files including small ones for --list
        all_session_files = find_session_files(projects_dir, cwd, min_size=0)
        list_sessions(all_session_files)
        return

    # Fix specific file
    if args.file:
        fix_session_file(args.file, create_backup=not args.no_backup)
        return

    # Fix by index
    if args.index is not None:
        if args.index < 1 or args.index > len(session_files):
            print(f"❌ Invalid index: {args.index} (valid range: 1-{len(session_files)})")
            sys.exit(1)
        fix_session_file(session_files[args.index - 1]["path"], create_backup=not args.no_backup)
        return

    # Fix all files
    if args.all:
        print(f"⚠️  About to fix {len(session_files)} session file(s).")
        print("   This will modify all session files and create backups.")
        try:
            confirm = input("\nProceed? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("Aborted.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return
        print()
        success = 0
        for f in session_files:
            if fix_session_file(f["path"], create_backup=not args.no_backup):
                success += 1
            print()
        print(f"\nDone: {success}/{len(session_files)} file(s) fixed successfully")
        return

    # Default: fix latest file
    if not session_files:
        # Check if there are small files that were skipped
        all_files = find_session_files(projects_dir, cwd, min_size=0)
        if all_files:
            print(f"❌ No session files found (skipped {len(all_files)} file(s) < 20KB)")
            print("   Use --list to see all files, or --file to fix a specific file")
        else:
            print("❌ No session files found")
        sys.exit(1)

    latest = session_files[0]
    print("🔧 Fixing latest session file:")
    print(f"   Path: {latest['path']}")
    print(f"   Size: {latest['size'] / 1024:.1f} KB")
    print(f"   Modified: {latest['mtime_str']}\n")

    fix_session_file(latest["path"], create_backup=not args.no_backup)

    print("\n💡 Tip: Restart Claude Code and run /resume to restore conversation")


if __name__ == "__main__":
    main()
