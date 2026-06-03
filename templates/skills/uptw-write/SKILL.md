---
name: uptw-write
description: Use only when the user explicitly invokes /UPTW-write to draft, continue, or revise an approved section inside a Windows-based Chinese urban-planning master's thesis project while protecting user edits and respecting frozen reasoning bounds.
---

# UPTW Write

This is one of exactly three user-visible UPTW skills: `uptw-init`, `uptw-plan`, and `uptw-write`.

Before writing, read:

- `references/skill-contract.md`
- `references/state-schema.md`
- `references/artifact-workflow.md`
- `references/writing-standards.md`
- `references/inference-boundaries.md`
- `references/chapter-evidence-alignment.md`

Load these when the section needs them:

- `references/chapter-function-bank.md`
- `references/reverse-outlining.md`
- `references/anti-template-patterns.md`
- `references/red-line-review.md`
- `references/rubric.md`

Use this skill only when the user explicitly chooses drafting, continuation, or revision.

## Expected Inputs

- Exact target chapter or section
- Allowed edit scope
- Source materials
- Target length or revision goal
- Any inline request text after `/UPTW-write`

If the target section or allowed scope is unclear, ask a concise question before writing.

## Workflow

1. Identify the exact section, target length, source materials, allowed edit range, and inline request after `/UPTW-write`.
2. Build a write context before any drafting:

```powershell
python .\scripts\workspace_artifact_tools.py build-write-context --workspace "<project-root>" --section "<chapter-section>"
```

3. Inspect the generated context.
   - If `can_write` is `false`, stop.
   - If blockers come from missing upstream outputs, insufficient evidence, or pending replan items, send the user back to `/UPTW-plan`.
4. Start a review cycle only after the context says the section is writable:

```powershell
python .\scripts\workspace_artifact_tools.py start-review-cycle --workspace "<project-root>" --docx "<thesis.docx>" --allowed-scope "<authorized edit range>" --context-file "<project-root>\.urban-planning-thesis-writer\state\current_write_context.json"
```

5. Snapshot the current DOCX before editing. If there is a previous snapshot, diff it so user changes can be detected and summarized.
6. Draft or revise only inside the authorized scope.
7. Before delivery or DOCX editing, verify:

- facts are grounded in user-provided materials
- reasoning strength does not exceed the frozen `reasoning_mode`
- terminology matches project state
- figures, tables, and formulas are introduced and interpreted properly
- section flow moves from evidence to interpretation to conclusion
- no generic significance padding, empty transitions, or AI-template phrasing survives

8. Review the completed draft and populate `completion.json` fields: `plan_validation`, `memory_decision`, notes. The `memory_decision` field carries stable_preferences, tentative_observations, rejected_generalizations, facts_confirmed, and open_questions.
9. Commit validated memory decisions to long-running state:

```powershell
python .\scripts\state_memory_tools.py remember-review --workspace "<project-root>" --section "<section>" --stable "<preference>" --tentative "<observation>" ...
```

Only record stable, explainable preferences. Do not over-generalize local edits. If intent is unclear, ask the user.
10. If structure is loose or repetitive, use reverse outlining before sentence-level polishing.
11. For near-final checks, use the red-line review stance: report only blocking issues.
12. When the user authorizes DOCX updates, prefer `scripts/docx_writer.py` helpers to inspect, insert, or append the prepared text block.
13. If the DOCX is locked by the user, stop and ask them to save and close it. Retry the same file after they confirm. Do not silently redirect output elsewhere.
14. If write-time work discovers a true replan trigger, queue it instead of improvising around it.
15. Close the review cycle and update project state after the writing pass.

## Writing Standards

- Arguments must unfold from materials and spatial evidence, not from slogan-like planning language.
- Keep long-form thesis texture: claim, evidence, interpretation, transition.
- Preserve analytic coverage when revising. Do not make prose feel more human by deleting content.
- Remove bad patterns specifically; do not "humanize" into chatty tone.
- Prefer no-op or light-touch revision when the text is already strong.

## Guardrails

- Do not start writing before a valid write context exists.
- Do not silently resolve blocked dependencies inside the write pass.
- Do not overwrite user-approved sections outside the authorized range.
- Do not expose internal memory bookkeeping unless the user asks.

## Return Style

Return only:

- the authorized scope
- whether the context allowed writing
- what was drafted or revised
- what remains blocked
- whether the DOCX was updated
