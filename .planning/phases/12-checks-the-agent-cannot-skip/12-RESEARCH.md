---
phase: 12-checks-the-agent-cannot-skip
created: 2026-09-29
sources: Claude Code's hooks reference, code.claude.com/docs/en/hooks, read on 2026-09-29; hpkit/interp.py and hpkit/lint.py
---

# Phase 12 research: what a hook can do here

`../11-the-working-folder/11-RESEARCH.md` read the same page on 2026-09-26
for a plugin. Read again for hooks in the kit's own `.claude/settings.json`;
where the two readings differ, this one says so.

## Events

- **PostToolUse** gets `tool_name`, `tool_input` (`file_path` for Write
  and Edit; `command` for Bash) and `tool_response`. **Exit 2 does not
  block it**: the table says "No | Shows stderr to Claude; the tool already
  ran". To speak without an error, `hookSpecificOutput.additionalContext`,
  which the page says goes "next to the tool result".
- **PreToolUse**: exit 2 "Blocks the tool call"; or
  `hookSpecificOutput.permissionDecision: "deny"` with a reason.
- **Stop** gets `last_assistant_message`, `transcript_path`, `cwd`. Exit 2,
  or `{"decision": "block", "reason": ...}`, keeps the agent going.
  **This reading found no limit on blocks in a row and no
  `stop_hook_active`**, where 11-RESEARCH recorded both. A Stop hook here
  has to keep itself out of a loop.
- Matchers filter by tool name: `Edit|Write`, `Bash`.

## Running a hook

- `CLAUDE_PROJECT_DIR` is "the project root where the session started".
- **Exec form**, `command` plus `args`, spawns with no shell;
  `${CLAUDE_PROJECT_DIR}` is written inside `args` in the page's own
  example. Shell form runs in Git Bash on Windows, or PowerShell without it,
  whose variables are written differently: exec form avoids that.
- **A hook that cannot start does not block**: the page's example is exit
  127, "Failed with non-blocking status code", and "for most hook events,
  the action proceeds". So on a machine where `python` does not start, the
  checks are off, with a notice.
- Timeout: 600 seconds by default for command hooks.
- Edits to hooks in settings files "are normally picked up automatically".

## Switching them off

`"disableAllHooks": true` in a settings file; the value left after
precedence applies, so a person's `.claude/settings.local.json` can turn off
what the kit's `.claude/settings.json` turns on.

## Open, to be settled by trying

1. **Whether hooks in a downloaded folder's `.claude/settings.json` run at
   once, or after a trust prompt.** The page states the dialog for a
   subagent's frontmatter hooks, not for settings files.
2. **Whether `python` in exec form starts on this machine**, where it is the
   Microsoft Store's alias.
3. **Whether a variable set in `env` of `.claude/settings.json` reaches the
   commands the agent runs through Bash.**

## The tools' own signals

- `hpprime lint` exits 1 when there is an error, 0 otherwise, and prints
  `N file(s): E error(s), W warning(s)`.
- `hpprime run` exits 0 when every `--call` answered, and 1 when the file
  does not load or a call raises, whether the program is wrong or the
  interpreter does not cover what it met: the exit code does not tell the two
  apart.
