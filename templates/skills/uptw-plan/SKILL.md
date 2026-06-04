---
name: uptw-plan
description: Use only when the user explicitly invokes /UPTW-plan to lock the thesis evidence boundary, chapter graph, section briefs, and replan queue for a Windows-based Chinese urban-planning master's thesis project.
---

# UPTW Plan

UPTW exposes two user-visible skills: `uptw-plan` and `uptw-write`.

Before planning, read:

- `references/skill-contract.md`
- `references/state-schema.md`
- `references/artifact-workflow.md`
- `references/plan-execution-harness.md`
- `references/chapter-function-bank.md`
- `references/chapter-evidence-alignment.md`
- `references/inference-boundaries.md`
- `references/writing-standards.md`

Load these only when needed during planning:

- `references/corpus-findings.md`
- `references/harness-design.md`
- `references/rubric.md`

Use this skill only when the user explicitly chooses planning or plan repair. On the first `/UPTW-plan` run for a thesis workspace, this skill must bootstrap the state tree itself before continuing.

## Expected Inputs

- Existing thesis DOCX when available
- Opening report, notes, experiment outputs, figures, tables, formulas, references, and user-confirmed conclusions
- Any inline request text after `/UPTW-plan`

If critical evidence is missing or the allowed planning scope is unclear, ask a concise question instead of filling the gap yourself.

## Execution Harness

Treat `/UPTW-plan` as a phased harness, not as one long free-form reasoning pass.

You must execute these phases in order:

1. `bootstrap`
2. `inventory`
3. `outline`
4. `briefs`

Before each new phase:

- read `state/progress.json` if it exists
- inspect `plan_state.current_phase`, `resume_from`, `completed_phases`, `target_sections`, and `latest_brief_batch`
- resume from the earliest incomplete phase instead of casually redoing the whole run

After each phase:

- persist the phase result before moving on
- update `state/progress.json.plan_state`
- leave a resume point if the request scope is too large for one uninterrupted pass

Large first-run requests must not be silently compressed. If the user asks for whole-thesis planning, continue in batches and persist each batch; do not collapse the task into a shallow overview just because the materials are numerous.

## Workflow

### Phase 1: Bootstrap

1. Identify the user's actual thesis project root and a usable Python executable or command.
   - If either is unclear and cannot be inferred safely, ask one short question.
2. Read any existing `state/progress.json` and determine whether this is a first run or a resumed planning run.
3. Mark bootstrap as in progress:

```powershell
python .\scripts\workspace_artifact_tools.py update-plan-progress --workspace "<project-root>" --phase bootstrap --status in_progress --summary "Bootstrap started"
```

4. If `<project-root>\.urban-planning-thesis-writer\state\` does not exist, initialize the workspace yourself before planning:

```powershell
.\scripts\init_thesis_workspace.ps1 -Workspace "<project-root>" -Python "<python.exe-or-python>"
```

5. Verify bootstrap state exists before any planning pass:

- `<project-root>\.urban-planning-thesis-writer\state\`
- `<project-root>\.urban-planning-thesis-writer\state\chapters\`
- `<project-root>\.urban-planning-thesis-writer\state\review-cycles\`
- `<project-root>\.urban-planning-thesis-writer\state\memory\`
- `<project-root>\.urban-planning-thesis-writer\state\snapshots\`
- `<project-root>\.urban-planning-thesis-writer\state\diffs\`
- `<project-root>\.urban-planning-thesis-writer\state\backups\`
- `<project-root>\.urban-planning-thesis-writer\logs\`
- `state/outline.json`
- `state/replan_queue.json`
- `state/memory/user_revision_preferences.json`
- `state/memory/section_memory.json`
- `state/memory/review_history.jsonl`
- `state/project.json`
- `state/material_inventory.json`
- `state/progress.json`

6. Mark bootstrap complete and record whether state was newly created or reused:

```powershell
python .\scripts\workspace_artifact_tools.py update-plan-progress --workspace "<project-root>" --phase bootstrap --status completed --summary "Bootstrap verified"
```

### Phase 2: Inventory

7. Mark inventory as in progress before reading materials:

```powershell
python .\scripts\workspace_artifact_tools.py update-plan-progress --workspace "<project-root>" --phase inventory --status in_progress --summary "Material inventory started"
```

8. Read the user's supplied materials and the inline request after `/UPTW-plan`.
9. Inventory the materials before attempting outline design.
   - Identify candidate thesis DOCX files, opening report, notes, experiment outputs, figures, tables, formulas, references, and any user-confirmed conclusions.
   - Do not treat file listing as sufficient. For each core material, extract at least one reusable result: a fact boundary, methodological note, key finding, figure/table/formula clue, or unresolved question.
   - If there are multiple plausible main DOCX files, stop and ask one short question instead of guessing.
10. If an existing DOCX will be inspected or may later be edited, snapshot it first:

```powershell
python .\scripts\docx_state_tools.py snapshot --workspace "<project-root>" --docx "<thesis.docx>" --label "plan"
```

11. Persist project-level facts as soon as they are clear:

```powershell
python .\scripts\workspace_artifact_tools.py upsert-project-state --workspace "<project-root>" --payload-file "<project-payload.json>"
```

12. Persist the material inventory before moving on, even if it is still partial and some files are deferred:

```powershell
python .\scripts\workspace_artifact_tools.py upsert-material-inventory --workspace "<project-root>" --payload-file "<inventory-payload.json>"
```

13. Extract and persist terminology from the inventoried materials — core terms, abbreviations, and variable names:

```powershell
python .\scripts\workspace_artifact_tools.py upsert-terminology --workspace "<project-root>" --payload-file "<terminology-payload.json>"
```

14. Record candidate docx files, the current docx, and resume notes:

```powershell
python .\scripts\workspace_artifact_tools.py update-plan-progress --workspace "<project-root>" --phase inventory --status completed --current-docx "<thesis.docx>" --material-inventory ".\.urban-planning-thesis-writer\state\material_inventory.json" --summary "Material inventory completed"
```

Do not advance to `outline` if core materials have only been skimmed or if the main DOCX remains ambiguous.

### Phase 3: Outline

15. Mark outline as in progress:

```powershell
python .\scripts\workspace_artifact_tools.py update-plan-progress --workspace "<project-root>" --phase outline --status in_progress --summary "Outline planning started"
```

16. If `state/replan_queue.json` contains pending items, review them before extending downstream plans.
17. Build or repair the global outline so it captures:

- main question
- section graph
- dependencies
- chapter functions
- global open questions
- current blockers

18. Persist the outline:

```powershell
python .\scripts\workspace_artifact_tools.py upsert-outline-section --workspace "<project-root>" --payload-file "<outline-payload.json>"
```

19. Record outline completion and any remaining blockers:

```powershell
python .\scripts\workspace_artifact_tools.py update-plan-progress --workspace "<project-root>" --phase outline --status completed --outline-path ".\.urban-planning-thesis-writer\state\outline.json" --summary "Outline updated"
```

### Phase 4: Briefs

20. Mark briefs as in progress:

```powershell
python .\scripts\workspace_artifact_tools.py update-plan-progress --workspace "<project-root>" --phase briefs --status in_progress --summary "Chapter brief generation started"
```

21. For every chapter or section likely to enter write mode, create or update a schema-v2 brief:

```powershell
python .\scripts\workspace_artifact_tools.py upsert-chapter-brief --workspace "<project-root>" --payload-file "<brief-payload.json>"
```

22. Freeze reasoning boundaries for each writable section:

- evidence anchors
- reasoning mode
- dependency inputs
- confirmed outputs
- open questions
- forbidden moves

23. If the request scope covers the full thesis or many sections, process briefs in batches and checkpoint every batch:

```powershell
python .\scripts\workspace_artifact_tools.py update-plan-progress --workspace "<project-root>" --phase briefs --brief-section "<section-a>" --brief-section "<section-b>" --target-section "<remaining-section>" --resume-from "continue-brief-batch" --summary "Saved latest brief batch"
```

24. If planning discovers unsupported judgments, missing upstream outputs, invalidated dependencies, or drift between chapter function and actual writing target, queue or repair replan items rather than pretending the section is ready.
25. Update project state after the planning pass: outline, briefs, pending blockers, figure or formula references, open questions, and any new terminology.
26. Only mark briefs complete when the requested planning scope has actually been covered. If the run stops mid-scope, leave a concrete resume point instead of pretending completion.

```powershell
python .\scripts\workspace_artifact_tools.py update-plan-progress --workspace "<project-root>" --phase briefs --status completed --summary "Requested brief scope completed"
```

## Planning Standards

- Do not promote a section into write-ready status without an evidence anchor and a bounded reasoning mode.
- Treat first-run bootstrap as part of planning, not a separate user-visible stage.
- Treat material inventory as a hard prerequisite for serious planning, not a courtesy step.
- When materials are numerous, persist partial extraction and continue in batches rather than reducing depth.
- Treat figures, tables, and formulas as evidence objects, not decoration.
- Extract and maintain a terminology registry: core terms, abbreviations, and variable names must be recorded in `terminology.json` so write mode can enforce consistency across chapters.
- Keep chapter functions explicit: diagnosis, method, result, mechanism, strategy, conclusion, and so on.
- Strategy language must still map back to diagnosis and evidence, not generic planning slogans.
- Use the corpus and writing references to constrain prose expectations, not to copy wording.
- When the user asks for whole-thesis planning, do not quietly downgrade to a single rough framework; keep going until the requested scope is covered or a real blocker requires a question.

## Guardrails

- Do not write full thesis sections in this skill unless the user explicitly asks for planning text artifacts rather than thesis prose.
- Do not claim planning succeeded if bootstrap state could not be created or verified.
- Do not claim inventory is complete if core materials were only browsed but not extracted.
- Do not let context pressure or repetition fatigue shorten the requested planning scope.
- Do not silently upgrade weak evidence into strong claims.
- Do not bypass pending replan items just to keep momentum.
- Do not expose internal bookkeeping that the user did not ask to see.

## Return Style

Return only:

- whether this run resumed from an existing phase checkpoint
- whether the workspace was bootstrapped just now or existing state was reused
- locked facts and evidence boundary
- section graph or scope that was updated
- current blockers
- unresolved questions
- next suggested command, normally `/UPTW-write` if the target section is writable
