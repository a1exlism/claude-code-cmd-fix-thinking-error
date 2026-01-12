# Claude Code Thinking Block 修复工具

修复 Claude Code API 错误 400 - thinking block 签名无效问题。

## 问题描述

在使用 Claude Code 的扩展思维模式时，可能会遇到以下错误：

```shell
API Error: 400 {"type":"error","error":{"type":"invalid_request_error","message":"messages.X.content.0: Invalid `signature` in `thinking`block"}}
```

这是由于会话文件中的 thinking blocks 损坏导致的。

## 解决方案

本工具可以从 Claude Code 会话文件中移除损坏的 `thinking` 和 `redacted_thinking` 块，让你能够恢复对话。

## 安装

### 快速安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/a1exlism/claude-code-cmd-fix-thinking-error.git
cd claude-code-cmd-fix-thinking-error

# 运行安装脚本
./install.sh
```

安装脚本会可选地配置 Claude Code hooks 以自动检查会话文件。

### 手动安装

```bash
# 复制修复脚本
cp fix_claude_thinking_error.py ~/.claude/

# 复制命令文件（可选，用于 /fix-thinking-error 命令）
mkdir -p ~/.claude/commands
cp commands/fix-thinking-error.md ~/.claude/commands/
```

## 使用方法

### 错误发生时（会话内修复）

当遇到 400 错误时，使用以下工作流在 Claude Code 内完成修复：

```bash
# 步骤 1：清除当前损坏的会话
/clear

# 步骤 2：修复会话文件
/fix-thinking-error

# 步骤 3：恢复修复后的会话
/resume
# 然后选择你要恢复的会话
```

> **说明**：`/clear` 会清除当前对话上下文，使 `/fix-thinking-error` 能够正常运行而不触发 400 错误。

### 方法一：直接运行 Python 脚本

```bash
# 修复最新会话（默认）
python3 ~/.claude/fix_claude_thinking_error.py

# 列出所有会话文件
python3 ~/.claude/fix_claude_thinking_error.py --list

# 修复所有会话文件
python3 ~/.claude/fix_claude_thinking_error.py --all

# 修复指定文件
python3 ~/.claude/fix_claude_thinking_error.py --file /path/to/session.jsonl

# 按索引修复（索引来自 --list）
python3 ~/.claude/fix_claude_thinking_error.py --index 2

# 跳过备份（谨慎使用）
python3 ~/.claude/fix_claude_thinking_error.py --no-backup
```

### 方法二：Claude Code 命令（安装后）

```bash
/fix-thinking-error           # 修复最新会话（默认）
/fix-thinking-error --list    # 列出所有会话文件
/fix-thinking-error --all     # 修复所有会话文件
```

> 注意：在 Claude Code 内使用 `/fix-thinking-error` 可能会产生新的 thinking blocks。如果修复后错误仍然存在，请在外部终端重新运行脚本。

### 使用 Hooks 自动修复

Claude Code hooks 是用户定义的 shell 命令，在生命周期的不同点自动执行。你可以配置 hook 在恢复会话时自动检查损坏的 thinking blocks。

在 `~/.claude/settings.json` 中添加以下配置：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "resume",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/fix_claude_thinking_error.py --hook-mode --cwd \"$CLAUDE_PROJECT_DIR\""
          }
        ]
      }
    ]
  }
}
```

该 hook 会在 `SessionStart` 事件（特别是恢复会话时）触发，检查会话文件是否有损坏的 thinking blocks。

## 命令选项

| 选项                     | 说明                       |
| ------------------------ | -------------------------- |
| `--list` / `-l`          | 列出所有会话文件           |
| `--file <path>` / `-f`   | 修复指定文件               |
| `--index <n>` / `-i`     | 按索引修复/恢复文件        |
| `--all` / `-a`           | 修复所有会话文件           |
| `--no-backup`            | 跳过备份创建（谨慎使用）   |
| `--auto-fix`             | 使用 --all 时跳过确认      |
| `--cwd <path>` / `-c`    | 按项目目录筛选会话         |
| `--check`                | 检查损坏的 thinking blocks |
| `--hook-mode`            | 作为 hook 运行，输出 JSON  |
| `--list-backups` / `-lb` | 列出所有备份文件           |
| `--restore` / `-r`       | 从备份恢复会话             |
| `--delete` / `-d`        | 恢复后删除备份文件         |

## 按项目筛选

当同时运行多个 Claude Code 实例时，使用 `--cwd` 按项目筛选会话：

```bash
# 仅修复当前项目的会话
python3 ~/.claude/fix_claude_thinking_error.py --cwd .

# 列出指定项目的会话
python3 ~/.claude/fix_claude_thinking_error.py --cwd /path/to/project --list

# 修复所有会话（所有项目）
python3 ~/.claude/fix_claude_thinking_error.py
```

> `/fix-thinking-error` 命令默认使用 `--cwd` 筛选当前项目。使用 `--global` 可修复所有项目。

## 备份与恢复

### 列出备份文件

```bash
python3 ~/.claude/fix_claude_thinking_error.py --list-backups
```

### 从备份恢复

```bash
# 恢复最新备份
python3 ~/.claude/fix_claude_thinking_error.py --restore

# 按索引恢复指定备份
python3 ~/.claude/fix_claude_thinking_error.py --restore --index 2

# 恢复后删除备份文件
python3 ~/.claude/fix_claude_thinking_error.py --restore --delete
```

## 修复后操作

**重要**：修复后必须重新加载会话。修复脚本只修改磁盘上的文件，不会更新当前会话的内存状态。

```bash
# 在 Claude Code 中重新加载会话
/resume
# 然后选择当前会话以重新加载
```

> ⚠️ **修复后请勿继续使用当前会话。** 错误会持续出现，直到你执行 `/resume` 重新加载修复后的会话数据。

## 工作原理

1. 定位 `~/.claude/projects/` 目录下的 Claude Code 会话文件
2. 创建带时间戳的备份（如 `session.jsonl.bak.20250109_120000`）
3. 从消息中移除 `thinking` 和 `redacted_thinking` 内容块
4. 写入清理后的会话文件

## 文件结构

```
claude-thinking-fix/
├── README.md                           # 英文文档
├── README_CN.md                        # 中文文档
├── install.sh                          # 安装脚本
├── fix_claude_thinking_error.py        # 主修复脚本
└── commands/
    └── fix-thinking-error.md           # Claude Code 命令文件
```

## 系统要求

- Python 3.6+
- 无外部依赖（仅使用标准库）

## 平台支持

| 平台     | 状态        | 说明                     |
|----------|-------------|--------------------------|
| Linux    | ✅ 支持     | 原生支持                 |
| macOS    | ✅ 支持     | 原生支持                 |
| WSL      | ✅ 支持     | Windows 用户推荐使用     |
| Windows  | ❌ 未测试   | 欢迎贡献                 |

## 参考

- [Issue #10199 - BUG: API Error 400 - Thinking Block Modification Error](https://github.com/anthropics/claude-code/issues/10199)

## 许可证

MIT License
