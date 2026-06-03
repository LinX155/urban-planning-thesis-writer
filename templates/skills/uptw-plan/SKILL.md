---
name: uptw-plan
description: Use only when the user explicitly invokes /UPTW-plan to lock the thesis evidence boundary, chapter graph, section briefs, and replan queue for a Windows-based Chinese urban-planning master's thesis project.
---

# UPTW Plan

This is one of exactly three user-visible UPTW skills: `uptw-init`, `uptw-plan`, and `uptw-write`.

Before planning, read:

- `references/skill-contract.md`
- `references/state-schema.md`
- `references/artifact-workflow.md`
- `references/chapter-function-bank.md`
- `references/chapter-evidence-alignment.md`
- `references/inference-boundaries.md`
- `references/writing-standards.md`

Load these only when needed during planning:

- `references/corpus-findings.md`
- `references/harness-design.md`
- `references/rubric.md`

Use this skill only when the user explicitly chooses planning or plan repair.

## Expected Inputs

- Existing thesis DOCX when available
- Opening report, notes, experiment outputs, figures, tables, formulas, references, and user-confirmed conclusions
- Any inline request text after `/UPTW-plan`

If critical evidence is missing or the allowed planning scope is unclear, ask a concise question instead of filling the gap yourself.

## Workflow

1. Read the user's supplied materials and the inline request after `/UPTW-plan`.
2. If an existing DOCX will be inspected or may later be edited, snapshot it first:

```powershell
python .\scripts\docx_state_tools.py snapshot --workspace "<project-root>" --docx "<thesis.docx>" --label "plan"
```

3. If `state/replan_queue.json` contains pending items, review them before extending downstream plans.
4. Build or repair the global outline so it captures:

- main question
- section graph
- dependencies
- chapter functions
- global open questions
- current blockers

5. For every chapter or section likely to enter write mode, create or update a schema-v2 brief:

```powershell
python .\scripts\workspace_artifact_tools.py upsert-chapter-brief --workspace "<project-root>" --payload-file "<brief-payload.json>"
```

6. Freeze reasoning boundaries for each writable section:

- evidence anchors
- reasoning mode
- dependency inputs
- confirmed outputs
- open questions
- forbidden moves

7. If planning discovers unsupported judgments, missing upstream outputs, invalidated dependencies, or drift between chapter function and actual writing target, queue or repair replan items rather than pretending the section is ready.
8. Update project state after the planning pass: outline, briefs, pending blockers, figure or formula references, and open questions.

## Planning Standards

- Do not promote a section into write-ready status without an evidence anchor and a bounded reasoning mode.
- Treat figures, tables, and formulas as evidence objects, not decoration.
- Keep chapter functions explicit: diagnosis, method, result, mechanism, strategy, conclusion, and so on.
- Strategy language must still map back to diagnosis and evidence, not generic planning slogans.
- Use the corpus and writing references to constrain prose expectations, not to copy wording.

## Guardrails

- Do not write full thesis sections in this skill unless the user explicitly asks for planning text artifacts rather than thesis prose.
- Do not silently upgrade weak evidence into strong claims.
- Do not bypass pending replan items just to keep momentum.
- Do not expose internal bookkeeping that the user did not ask to see.

## Return Style

Return only:

- locked facts and evidence boundary
- section graph or scope that was updated
- current blockers
- unresolved questions
- next suggested command, normally `/UPTW-write` if the target section is writable
