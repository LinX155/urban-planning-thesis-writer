---
name: uptw
description: Use only when the user explicitly invokes /UPTW, /UPTW-init, /UPTW-plan, or /UPTW-write for Windows-based Chinese urban and rural planning master's thesis writing. This skill turns already completed experiments, analysis, data processing, figures/tables/formulas, and confirmed conclusions into an evidence-grounded long-form DOCX workflow. Use it to initialize the workspace, lock a thesis plan, or write and revise approved sections inside an existing thesis project. It must not propose topics, design experiments, invent methods, fabricate findings, or write beyond user-provided evidence.
---

# Urban Planning Thesis Writer

This skill is a Windows-first, DOCX-centered writing harness for Chinese urban-planning master's theses. It stays inactive unless the user explicitly calls one of its slash commands.

## Mission

This skill has three obligations:

1. Human academic prose discipline. Keep the thesis readable as a human-written graduate paper with evidence-first argument flow, restrained academic Chinese, stable terminology, and no empty template language.
2. Urban-planning specialization. Optimize for Chinese urban and rural planning thesis conventions, especially spatial scale, planning object definition, figure/table/formula explanation, model-to-strategy mapping, and planning-oriented chapter logic.
3. Durable long-form collaboration. Persist the argument graph, chapter briefs, write contexts, review cycles, user revision memory, and re-plan blockers on disk so the workflow survives long sessions and user edits.

When these obligations conflict with generic fluency advice or generic writing habits, prefer the obligations above.

## What This Skill Does

- Organize already completed research into a long-form thesis DOCX.
- Keep long-running collaboration stable across sessions by storing outline, chapter briefs, write contexts, snapshots, diffs, backups, review-cycle artifacts, and re-plan queue items on disk.
- Draft, continue, or revise only the chapter or section the user has authorized, while protecting reviewed content and user edits.

## What This Skill Does Not Do

- Topic selection
- Research design
- New data-analysis method design
- Result fabrication
- Citation fabrication
- Writing past the user's confirmed facts, materials, scope, or conclusions

## Command Routing

Use the command literally as entered by the user:

- The user may append inline instructions after `/UPTW-plan` or `/UPTW-write`.
- Treat everything after the slash command as the request body for that phase.
- Example: `/UPTW-write revise 4.2 within 1200 Chinese characters and keep the existing terminology`.

| Command | Use it for | Required behavior |
| --- | --- | --- |
| `/UPTW` | The user wants this skill but has not yet chosen a phase | Load the skill, confirm whether the user wants init, plan, or write, and do not start thesis work yet |
| `/UPTW-init` | Workspace initialization | Initialize the Windows workspace state and dependencies |
| `/UPTW-plan` | Planning before drafting or repairing a blocked plan | Read the user's materials, lock or repair the thesis plan, and prepare section-level constraints |
| `/UPTW-write` | Drafting, continuation, or revision | Build the write context first, stop if blockers exist, otherwise write or revise the approved chapter or section while protecting user edits |

Do not create extra user-visible subskills for quality review, figure or formula checks, anti-template checks, consistency checks, uncertainty handling, write-context building, re-plan queue handling, or backups. Run those as internal mechanisms during plan and write.

## Key Design Ideas

Use these ideas to keep the workflow disciplined:

- Evidence first. Existing DOCX, figures, tables, formulas, notes, outputs, and user-confirmed conclusions outrank chat speculation.
- Brownfield first. Treat the current thesis project as the working system. Extend and protect it; do not replace it with a fresh, chat-only rewrite.
- Artifact first. Persist important decisions in outline, chapter briefs, write contexts, review cycles, state files, snapshots, re-plan queue, and memory files instead of relying on chat history alone.
- Memory with proof. Promote only evidence-backed preferences and facts into long-running memory. Do not generalize one-off edits.
- Re-plan before rewrite. When structure, dependencies, or reasoning bounds fail, repair the plan instead of improvising inside `/UPTW-write`.

## Hard Boundaries

- Use this skill only after the user has already completed experiments, analysis, data processing, and main conclusions.
- Never invent research facts, experimental results, model outputs, spatial findings, case details, data sources, numeric results, citations, or policy implications.
- Never provide topic selection, experiment design, new data-analysis methods, or result fabrication.
- Never copy thesis corpus wording into reusable sentence templates. Generalize structure and constraints only.
- Treat the DOCX as the source of truth after the user reviews it. Snapshot before work and preserve user-approved content.
- If direct DOCX editing fails because the user still has the file open in Word or another editor, ask the user to save and close the DOCX first, then continue. Do not silently switch to a backup copy, `save as`, or a new sibling DOCX unless the user explicitly requests that fallback.
- Work on Windows. Prefer PowerShell and Python scripts in `scripts/`; do not require bash.

## Suggested User Flow

The normal collaboration order is:

1. `/UPTW-init`
2. `/UPTW-plan`
3. `/UPTW-write`
4. Repeat `/UPTW-write` for later sections and revision rounds
5. If `/UPTW-write` finds blockers, return to `/UPTW-plan` to repair the plan before continuing

Use `/UPTW-plan` to establish a stable writing frame before heavy drafting. Do not jump straight into full-length chapter writing unless the user explicitly accepts that risk.

## Inputs by Phase

Expect these materials when possible:

| Phase | Typical inputs |
| --- | --- |
| `init` | Thesis project root, Python executable |
| `plan` | Existing DOCX, opening report, figures, tables, formulas, experiment outputs, confirmed conclusions |
| `write` | Exact target section, allowed edit scope, source materials, target length, and any newly reviewed user changes |

If required evidence is missing or the allowed scope is unclear, ask a concise question instead of filling the gap yourself.

## Reference Loading

Load only what is needed:

- `references/corpus-findings.md`: Writing commonalities distilled from the thesis PDF corpus.
- `references/writing-standards.md`: Detailed academic prose, chapter, figure/table, formula, and anti-template constraints.
- `references/inference-boundaries.md`: What evidence allows which reasoning strength.
- `references/harness-design.md`: Long-form harness design constraints distilled from external Chinese academic-writing references.
- `references/artifact-workflow.md`: Global argument graph, chapter briefs, write contexts, re-plan queue, and review-cycle artifacts.
- `references/chapter-function-bank.md`: Chapter-function guidance adapted to long-form master's theses rather than short conference papers.
- `references/chapter-evidence-alignment.md`: Internal planning check for chapter judgments, evidence anchors, reasoning mode, and unsupported gaps.
- `references/reverse-outlining.md`: Section-level flow check for long paragraphs and long chapters.
- `references/red-line-review.md`: High-tolerance final check that reports only blocking issues.
- `references/anti-template-patterns.md`: Concrete bad-pattern list for removing template language without weakening academic rigor.
- `references/state-schema.md`: Project state files, schema-v2 structure, and memory rules.
- `references/rubric.md`: Self-check rubric before delivery or major updates.

Creation-only corpus extraction files and subagent notes are not part of normal use. Use only the condensed reference files above during regular operation.

## Init Workflow

Run this section on `/UPTW-init`.

1. When the user enters `/UPTW-init` in Codex, execute the initialization yourself. Do not ask the user to open PowerShell and run commands manually unless automatic execution fails or the user explicitly asks for the raw command.
2. Locate the user's thesis project root and Python executable.
   - The project root is the user's thesis project folder where the DOCX, notes, figures, and other research materials live.
   - It must not be the `urban-planning-thesis-writer/` skill directory itself or any child path under it.
3. Run:

```powershell
.\urban-planning-thesis-writer\scripts\init_thesis_workspace.ps1 -Workspace "<project-root>" -Python "<python.exe-or-python>"
```

4. Verify `<project-root>\.urban-planning-thesis-writer\` exists with `state/`, `state/chapters/`, `state/write-contexts/`, `state/review-cycles/`, `state/memory/`, `state/snapshots/`, `state/diffs/`, `state/backups/`, and `logs/`.
5. Confirm the long-running memory files exist: `state/memory/user_revision_preferences.json`, `state/memory/section_memory.json`, and `state/memory/review_history.jsonl`.
6. Confirm schema-v2 bootstrap files exist: `state/outline.json` and `state/replan_queue.json`.
7. Tell the user only the initialized state path and the next suggested command. Do not expose internal diff or memory logic unless asked.

## Plan Workflow

Run this section on `/UPTW-plan`.

1. Read the user's supplied materials and any inline request text that followed `/UPTW-plan`: existing DOCX, opening report, experiment notes, analysis outputs, figures, tables, formulas, references, and any final conclusions.
2. Snapshot any existing DOCX before extracting or editing:

```powershell
python .\urban-planning-thesis-writer\scripts\docx_state_tools.py snapshot --workspace "<project-root>" --docx "<thesis.docx>" --label "plan"
```

3. If `state/replan_queue.json` has pending items, review them first and repair the plan before new drafting decisions.
4. Establish and write or update project state:
   - confirmed thesis title, research object, spatial and temporal scope;
   - main research question;
   - non-fabrication boundary: what facts, data, and conclusions are user-provided;
   - section graph: function, dependencies, downstream consumers, and status;
   - terminology, abbreviations, variable names, figure/table/formula list;
   - open questions that must be asked before writing;
   - for network studies: node, edge, weight, direction, threshold, time window, and data boundary;
   - for model studies: input data, variables, parameters, evaluation metrics, interpretation method, and scale definition;
   - for strategy chapters: diagnosis-evidence-mechanism-object-tool-effect-boundary mapping.
5. Upsert the argument graph in `outline.json`:

```powershell
python .\urban-planning-thesis-writer\scripts\workspace_artifact_tools.py upsert-outline-section --workspace "<project-root>" --payload-file "<outline-payload.json>"
```

6. For every chapter or section likely to enter `/UPTW-write`, create or update a schema-v2 brief:

```powershell
python .\urban-planning-thesis-writer\scripts\workspace_artifact_tools.py upsert-chapter-brief --workspace "<project-root>" --payload-file "<brief-payload.json>"
```

7. Use `references/chapter-function-bank.md`, `references/chapter-evidence-alignment.md`, and `references/inference-boundaries.md` together:
   - confirm the section function;
   - define 1 to 3 `core_judgments`;
   - assign `reasoning_mode` to each judgment;
   - bind each judgment to evidence anchors;
   - mark unsupported items as `open_question` or `do_not_write`;
   - define `dependency_inputs`, `confirmed_outputs`, `section_skeleton`, `transition_in`, `transition_out`, and `replan_watchpoints`.
8. Discuss chapter themes and strategy with the user. Keep the output concise and decision-oriented.
9. Do not draft full thesis text in plan mode unless the user explicitly asks for a tiny illustrative sample.

Normal outputs from plan mode are a confirmed fact boundary, a usable argument graph, schema-v2 briefs, terminology alignment, reasoning-mode assignments, and a short list of unresolved questions.

## Write Workflow

Run this section on `/UPTW-write`.

1. Identify the exact chapter or section, target length, source materials, allowed edit range, and any inline request text that followed `/UPTW-write`.
2. Build the write context first. The output must be a frozen plan context, not a fresh plan:

```powershell
python .\urban-planning-thesis-writer\scripts\workspace_artifact_tools.py build-write-context --workspace "<project-root>" --section "<chapter-section>" --output "<project-root>\.urban-planning-thesis-writer\state\write-contexts\<section>.json"
```

3. Inspect the resulting `context.json`.
   - If `can_write` is `false`, stop the write pass.
   - If blockers come from missing upstream outputs, insufficient evidence, or pending re-plan items, return to `/UPTW-plan`.
4. Start a review-cycle artifact only after the context says the section is writable:

```powershell
python .\urban-planning-thesis-writer\scripts\workspace_artifact_tools.py start-review-cycle --workspace "<project-root>" --docx "<thesis.docx>" --allowed-scope "<authorized edit range>" --context-file "<project-root>\.urban-planning-thesis-writer\state\write-contexts\<section>.json"
```

5. Snapshot the current DOCX before writing. If a previous snapshot exists, diff it against the current snapshot to detect user changes:

```powershell
python .\urban-planning-thesis-writer\scripts\docx_state_tools.py diff --workspace "<project-root>" --before "<old-snapshot.txt>" --after "<new-snapshot.txt>" --label "user-review"
python .\urban-planning-thesis-writer\scripts\docx_state_tools.py summarize-diff --workspace "<project-root>" --diff "<diff-file>" --output "<project-root>\.urban-planning-thesis-writer\state\memory\review-summaries\<review-summary>.json"
```

6. Interpret user changes cautiously:
   - record stable terminology, structure, citation, figure/table, or academic-style preferences;
   - do not generalize one-off local edits;
   - ask the user when the revision reason is unclear and would affect future writing.
7. Persist long-running memory before the next writing pass. Record only evidence-backed preferences, tentative signals, rejected over-generalizations, confirmed facts, and open questions:

```powershell
python .\urban-planning-thesis-writer\scripts\state_memory_tools.py remember-review --workspace "<project-root>" --section "<chapter-section>" --summary-file "<project-root>\.urban-planning-thesis-writer\state\memory\review-summaries\<review-summary>.json" --stable "<stable preference>" --tentative "<possible preference>" --rejected "<do not generalize this edit>" --fact "<user-confirmed fact>" --question "<ask later if still unresolved>"
```

This memory update is an internal mechanism of `/UPTW-write`. Do not expose the bookkeeping unless the user asks.

8. Write only inside the agreed scope. Preserve user-approved sections and avoid rewriting already reviewed content.
9. When a section feels loose, repetitive, or overlong, load `references/reverse-outlining.md` and repair structure before sentence-level polishing. For major claims in fragile sections, make sure the paragraph can still be mapped back to the frozen `core_judgment`, `reasoning_mode`, and visible evidence anchor.
10. Before presenting output or editing DOCX, run internal checks:
   - facts are grounded in user-provided materials;
   - no invented data, results, citations, or policy claims;
   - reasoning strength does not exceed `reasoning_mode`;
   - terminology and variables match state files;
   - figures, tables, and formulas are introduced before appearance and interpreted after appearance;
   - models and network indicators explain their data, variables, meaning, and limits;
   - strategy language names a checkable object, spatial unit, evidence source, and tool;
   - section flow moves from evidence to interpretation to conclusion;
   - each long paragraph can be reverse-outlined to one stable paragraph task, even if the paragraph is longer than conference-paper prose;
   - prose avoids empty transitional language, excessive bulleting, public-account tone, and generic significance or reference claims;
   - prose does not silently upgrade `open_question` into established fact;
   - prose does not silently resolve a blocked dependency inside the write pass.
11. For near-final passes, load `references/red-line-review.md` and use its high-tolerance stance: report blocking issues only, and do not create style noise when no red-line issue exists.
12. When the user authorizes direct DOCX writing, write only the prepared text block with `scripts/docx_writer.py`. Prefer `inspect` first to confirm headings, tables, section count, header/footer text, and styles, then `insert-after-heading` or `append`.
    - If the DOCX cannot be saved because the file is open or locked by the user, stop the write pass and ask the user to save and close the DOCX first.
    - After the user confirms the DOCX is closed, retry the intended edit against the same authorized file.
    - Do not silently work around the lock by saving to a backup path, creating a second DOCX, or redirecting output to a different filename unless the user explicitly asks for that behavior.
13. If the write pass discovers one of the fixed re-plan triggers, queue it instead of improvising:

```powershell
python .\urban-planning-thesis-writer\scripts\workspace_artifact_tools.py queue-replan --workspace "<project-root>" --payload-file "<replan-item.json>"
```

Use this only when:
   - upstream `confirmed_outputs` are missing or overturned;
   - the current evidence cannot support a frozen `core_judgment`;
   - user revisions invalidate a downstream dependency;
   - actual writing drifts away from `function / section_skeleton / transition_out`.

14. Close the review-cycle artifact with `plan_validation`, any new `confirmed_outputs`, and the final section status:

```powershell
python .\urban-planning-thesis-writer\scripts\workspace_artifact_tools.py complete-review-cycle --workspace "<project-root>" --cycle-dir "<cycle-dir>" --status "reviewed" --plan-validation-file "<plan-validation.json>" --confirmed-output "<new confirmed output>" --section-status "reviewed" --snapshot "<latest-snapshot>" --backup "<latest-backup>" --diff-summary "<project-root>\.urban-planning-thesis-writer\state\memory\review-summaries\<review-summary>.json" --memory-summary "<project-root>\.urban-planning-thesis-writer\state\memory\review_history.jsonl" --output-docx "<thesis.docx>"
```

15. Update state after the writing pass: progress, section status, confirmed outputs, figure/formula references, open questions, cautious memory, and any newly queued re-plan item ids.

## Writing Discipline

Read `references/writing-standards.md` before major writing. Use these rules even if that file is not loaded:

- Build arguments through materials and spatial evidence. Do not announce conclusions before proof.
- Link every planning strategy to a preceding diagnosis or finding.
- Keep long-form thesis texture. Paragraphs should develop a claim, evidence, interpretation, and transition instead of collapsing into bullet-like summaries.
- Use `references/chapter-function-bank.md` to match each chapter and section to its writing function. Reuse function logic, not reusable sentence templates.
- Use `references/chapter-evidence-alignment.md` to confirm whether a judgment is writable at all.
- Use `references/inference-boundaries.md` to confirm how far the evidence allows the judgment to go.
- Use tables and figures as evidence, not decoration.
- Introduce formulas by purpose, then explain variables, units, calculation object, and how the result will be used.
- Prefer restrained academic Chinese. Avoid rhetorical flourish, slogan-like planning language, repeated generic significance claims, and AI-like paragraph templates.
- In plan mode, do not promote a chapter judgment into writable prose until it has an evidence anchor, a reasoning mode, or an explicit `open_question` status.
- Revise AI-like writing by removing specific bad patterns, not by making the prose casual. The target is disciplined academic writing, not a chatty or personalized voice.
- Preserve legitimate academic formality. Do not "humanize" by adding personality, first-person commentary, humor, deliberate messiness, or conversational filler.
- Preserve information coverage when revising. Do not make the draft feel more natural by silently deleting analytic content, caveats, figure interpretation, or methodological explanation.
- Prefer a pass-through decision when the text is already strong. Do not optimize for visible change.
- When flow is unclear, fix outline-level relations before editing word choice. Use reverse outlining for structure, red-line review for near-final blocking checks, and ordinary polishing only after both are satisfied.

## Recovery

When a session resumes:

1. Read `.urban-planning-thesis-writer/state/progress.json`.
2. Read `.urban-planning-thesis-writer/state/replan_queue.json`.
3. Read `.urban-planning-thesis-writer/state/memory/user_revision_preferences.json` and `.urban-planning-thesis-writer/state/memory/section_memory.json`.
4. Read the relevant chapter brief in `.urban-planning-thesis-writer/state/chapters/`.
5. If the target section is likely to re-enter writing, rebuild its write context before continuing:

```powershell
python .\urban-planning-thesis-writer\scripts\workspace_artifact_tools.py build-write-context --workspace "<project-root>" --section "<chapter-section>" --output "<project-root>\.urban-planning-thesis-writer\state\write-contexts\<section>.json"
```

6. Inspect the latest review cycle:

```powershell
python .\urban-planning-thesis-writer\scripts\workspace_artifact_tools.py latest-cycle --workspace "<project-root>" --section "<chapter-section>"
```

7. Compare the current DOCX with the latest snapshot before continuing.
8. Continue only from the confirmed outline, brief, frozen reasoning bounds, and unresolved questions. Do not assume stale memory is correct.

## Minimal Return Style

Keep user-facing responses concise, decision-oriented, and grounded in the current phase:

- `init`: confirm the state path and the next command.
- `plan`: summarize the locked facts, section graph, section focus, blockers, and unresolved questions.
- `write`: summarize the authorized scope, whether the context allowed writing, what was drafted or revised, what remains blocked, and whether the DOCX was updated.
