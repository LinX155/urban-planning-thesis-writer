---
name: uptw-init
description: Use only when the user explicitly invokes /UPTW-init to initialize a Windows thesis workspace for UPTW. It prepares the project-level state tree, verifies required files, and gets the thesis project ready for plan and write without inventing research content.
---

# UPTW Init

This is one of exactly three user-visible UPTW skills: `uptw-init`, `uptw-plan`, and `uptw-write`.

Before doing anything else, read:

- `references/skill-contract.md`
- `references/state-schema.md`

Use this skill only when the user explicitly chooses initialization.

## Required Inputs

- The user's thesis project root
- A usable Python executable or command

The thesis project root must be the user's actual working thesis folder. It must not be this skill directory or any child path under it.

## Workflow

1. Identify the thesis project root and Python executable.
   - If either is unclear and cannot be inferred safely, ask one short question.
2. Run the initializer yourself. Do not ask the user to manually execute PowerShell unless automatic execution fails or the user explicitly asks for the raw command.

```powershell
.\scripts\init_thesis_workspace.ps1 -Workspace "<project-root>" -Python "<python.exe-or-python>"
```

3. Verify the project state directory exists:

- `<project-root>\.urban-planning-thesis-writer\state\`
- `<project-root>\.urban-planning-thesis-writer\state\chapters\`
- `<project-root>\.urban-planning-thesis-writer\state\review-cycles\`
- `<project-root>\.urban-planning-thesis-writer\state\memory\`
- `<project-root>\.urban-planning-thesis-writer\state\snapshots\`
- `<project-root>\.urban-planning-thesis-writer\state\diffs\`
- `<project-root>\.urban-planning-thesis-writer\state\backups\`
- `<project-root>\.urban-planning-thesis-writer\logs\`

4. Verify bootstrap state files exist:

- `state/outline.json`
- `state/replan_queue.json`
- `state/memory/user_revision_preferences.json`
- `state/memory/section_memory.json`
- `state/memory/review_history.jsonl`

5. If initialization fails because dependencies cannot be installed or the workspace path is invalid, stop and explain the blocker directly.

## Guardrails

- Do not initialize inside the skill repo.
- Do not silently redirect initialization to another folder.
- Do not claim initialization succeeded unless the state tree and bootstrap files actually exist.
- Do not start plan or write work in this skill.

## Return Style

Return only:

- the initialized state path
- the next suggested command, normally `/UPTW-plan`
