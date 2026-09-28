---
phase: 11-the-working-folder
superseded: in part, on 2026-09-26, when the plugin gave way to the kit's own folder
created: 2026-09-26
sources: Claude Code documentation, code.claude.com/docs/en, read on 2026-09-26
---

# Phase 11 research: how a Claude Code plugin works

Read from Claude Code's documentation on 2026-09-26, before anything is
built on it, as the milestone's context requires. Each point names the page
it came from; what the pages leave open is listed at the end, to be settled
by trying it, not assumed.

**Kept as the record of what was read.** The plugin was dropped on
2026-09-26, before it was installed (`../../milestone-2-CONTEXT.md`,
decision 1). What still holds is what Phase 12 builds on: **Hooks**, and
**Skills** and **Subagents** as they apply to a project's `.claude/`
folder. The layout, paths, install and open points 1, 3 and 4 were about
the plugin; point 2, which Python a hook can count on, is still open.

## Layout

From `plugins-reference` and `plugins/components`:

- `.claude-plugin/plugin.json` is the manifest. It is **optional**, and
  `name`, kebab-case, is its only required field. Every other file sits at the
  plugin root, not inside `.claude-plugin/`.
- Default locations: `skills/<name>/SKILL.md`, `agents/*.md`,
  `hooks/hooks.json`, `commands/*.md`, `bin/`, `settings.json`, `.mcp.json`.
- **A plugin with `SKILL.md` at its root, no `skills/` and no `skills` key
  loads as a single skill.** This repository has exactly that today.
- `bin/`: its files are on the Bash tool's `PATH` while the plugin is
  enabled. claude.ai and Cowork do not install a plugin that has one.
- A `CLAUDE.md` at the plugin root is not loaded, and validation warns about
  it. Instructions that must load go in a skill.
- Every component path must start with `./`, resolve inside the plugin root
  and exist.

## Paths at run time

From `plugins-reference`, "Environment variables":

- `${CLAUDE_PLUGIN_ROOT}` is the absolute path of the installed version. It
  resolves inside hook `command` and `args`, and inline anywhere in a skill's,
  command's or agent's Markdown body. **It is not in the environment of
  commands the agent runs through Bash**: a skill has to write the path into
  its text for the agent to use.
- `${CLAUDE_PLUGIN_DATA}` survives updates; `${CLAUDE_PLUGIN_ROOT}` changes
  with each, so nothing is written there.
- On Windows the substituted paths use forward slashes.

## Install, copy, update

From `plugins/create-marketplace`, `plugins/marketplace-reference`,
`plugins/install` and `plugins/loading`:

- A marketplace is a directory with `.claude-plugin/marketplace.json`: a
  `name`, an `owner` and a `plugins` array, each entry a `name` and a
  `source`. A relative `source` resolves from the marketplace root, starts
  with `./`, and may not contain `..`.
- Added by `/plugin marketplace add owner/repo` in a session, and installed
  by `/plugin install <plugin>@<marketplace>`. In one command, from v2.1.275:
  `/plugin install <plugin> --marketplace owner/repo`. The desktop app's
  Code tab does it through **+ > Plugins > Add plugin**. Scopes: user,
  project, local.
- On install, a marketplace plugin is **copied** to
  `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, and files
  outside the plugin directory are not copied. `--plugin-dir` loads a
  directory in place, which is how a plugin is tried before it is published.
- **The version**: the manifest's `version` first, then the entry's; with
  neither, a git-hosted plugin's version is its commit's SHA, so every
  commit reaches users. A pinned `version` keeps them on it until the string
  changes.

## Skills

From `skills`:

- Frontmatter between `---` lines; every field optional, `description`
  recommended. `description` and `when_to_use` together are cut at 1,536
  characters in the listing Claude reads.
- `paths` limits automatic loading to files matching globs;
  `disable-model-invocation` keeps a skill to `/name` only; `allowed-tools`
  pre-approves tools for the turn.
- A plugin skill's command is namespaced by the plugin: `/<plugin>:<skill>`.

## Subagents

From `sub-agents`:

- A Markdown file with frontmatter; `name` is required and may not contain
  `:`.
- **A plugin's subagents ignore `hooks`, `mcpServers` and `permissionMode`.**
  Their tools and model can be set; the checks of Phase 12 cannot live in an
  agent's frontmatter, and go in the plugin's `hooks/hooks.json`.

## Hooks

From `hooks`:

- A command hook gets the event as JSON on stdin. **Exit 2 blocks**, with
  stderr as the reason; any other non-zero exit is a non-blocking error; exit
  0 with JSON on stdout can decide instead.
- `PostToolUse` runs after the tool succeeded: it cannot undo the edit, but
  exit 2 or `"decision": "block"` puts its reason in front of Claude. File
  paths arrive absolute, with backslashes on Windows.
- `Stop` runs when the agent finishes; it receives `last_assistant_message`
  and `stop_hook_active`, and blocking makes the agent continue. Claude Code
  overrides the ninth consecutive block and ends the turn.
- **Exec form**, `command` plus `args`, spawns the executable with no shell,
  and is what the page recommends when a path placeholder is involved. Shell
  form runs in `sh`, in Git Bash on Windows, or in PowerShell when Git Bash
  is not installed. `timeout` defaults to 600 seconds.

## Open, to be settled by trying it

1. **Whether a plugin can be the root of its own marketplace**, with
   `"source": "./"`. The pages neither show nor forbid it. The alternative is
   the plugin in a subdirectory, which then has to hold the tools and the
   documentation itself, since nothing outside it is copied.
2. **Which `python` a hook can count on.** Exec form needs an executable on
   `PATH`; this machine has `python` from the Windows Store alias. `py` and
   `python3` differ by machine.
3. **Whether `bin/` works for the agent on Windows**, where the Bash tool is
   Git Bash: a shell script there would run, a `.cmd` may not.
4. **The Claude Code version on this machine.** `claude` is not on `PATH`:
   the user works in the desktop app, which installs plugins through its own
   menu. The one-command install needs v2.1.275 or later.
