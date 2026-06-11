---
name: uptw-write
description: Use only when the user explicitly invokes /UPTW-write to draft, continue, or revise an approved section inside a Windows-based Chinese urban-planning master's thesis project while protecting user edits and respecting frozen reasoning bounds.
---

# UPTW Write

UPTW exposes two user-visible skills: `uptw-plan` and `uptw-write`.

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
2. Build a write context before any drafting. This injects the project terminology table (`terminology.json`) into the context so this section's writing stays consistent with established terms:

```powershell
python .\scripts\workspace_artifact_tools.py build-write-context --workspace "<project-root>" --section "<chapter-section>"
```

3. Inspect the generated context.
   - Review the `terminology` field for the current term, abbreviation, and variable registry.
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
- terminology matches the frozen context: core terms use the same names defined in the context's `terminology` field; abbreviations are expanded on first use; variable names are consistent with the registry
- figures, tables, and formulas are introduced and interpreted properly
- formulas are preceded by natural-language descriptions of the derivation logic; variable symbols are used only when necessary, with simple quantities expressed in Chinese
- every variable in an inline formula is explained in parentheses on first appearance; display formulas are followed by a dedicated line explaining each variable
- thresholds mentioned in the text include an explanation of their meaning and the rationale for the chosen value
- Chinese expressions are checked for ambiguity and rewritten where multiple interpretations are possible
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
12. When the user authorizes DOCX updates, use `scripts/docx_writer.py` as a set of editing primitives rather than a fixed case table.
    - Inspect the target structure first.
    - Choose the smallest operation that satisfies the frozen write context and authorized scope.
    - Prefer rewriting existing prose in place when layout continuity matters.
    - Preserve non-text anchors such as images or page-break carriers in place whenever the writing task is about surrounding prose rather than those objects themselves.
    - Use insertion or append only when the writing task is truly additive rather than a revision of existing body text.
13. If the DOCX is locked by the user, stop and ask them to save and close it. Retry the same file after they confirm. Do not silently redirect output elsewhere.
14. If write-time work discovers a true replan trigger, queue it instead of improvising around it.
15. Close the review cycle and update project state after the writing pass.

## Writing Standards

- Arguments must unfold from materials and spatial evidence, not from slogan-like planning language.
- Keep long-form thesis texture: claim, evidence, interpretation, transition.
- Preserve analytic coverage when revising. Do not make prose feel more human by deleting content.
- Remove bad patterns specifically; do not "humanize" into chatty tone.
- Prefer no-op or light-touch revision when the text is already strong.
- When writing about formulas or calculations, narrate the derivation logic in natural language first; use symbols only when the expression is complex or will be referenced later. Do not introduce variable symbols for quantities that can be clearly stated in Chinese.
- Do not deliberately complicate language for the sake of sounding academic. Clear and direct prose is preferred over convoluted phrasing.

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
