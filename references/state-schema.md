# 项目级状态目录（Schema v2）

首次 `/UPTW-plan` 会在用户论文项目根目录创建 `.urban-planning-thesis-writer/`。该目录用于长文协作，不应当直接展示给用户，除非用户要求查看。它既保存长期状态，也保存章节工件、写作上下文、replan 队列和每轮审阅工件。

## 目录

- `state/project.json`：论文题目、研究对象、范围、不可编造的信息边界、当前 docx。
- `state/material_inventory.json`：首次 plan 的材料盘点账本，记录候选 docx、已深读/仅索引/暂缓处理的材料，以及从每份材料提取出的证据线索。
- `state/outline.json`：schema v2 的全局论证图，含 `main_question`、`sections[]`、`global_open_questions`。
- `state/replan_queue.json`：pending / resolved 的 replan item。
- `state/chapters/*.json`：每个章节或小节的 v2 brief。
- `state/current_write_context.json`：最新一轮写作的冻结上下文（覆盖式，从信源派生）。
- `state/terminology.json`：术语、缩写、变量命名和统一称谓。

- `state/memory/user_revision_preferences.json`：稳定偏好、暂存观察、已拒绝泛化项，以及最近一次审阅的章节。
- `state/memory/section_memory.json`：按章节累计的稳定偏好、暂存观察、已确认事实和待确认问题。
- `state/memory/review_history.jsonl`：每轮审阅的事件日志，含差异摘要和本轮记忆结论。
- `state/review-cycles/<timestamp>-<section>/`：每轮 `/write` 的工件目录，包含 `request.json`、`completion.json`、可选的 `context.json`。
- `state/progress.json`：已完成章节、待完成章节、blocked sections、pending replan items、最近快照、最近备份、审阅轮次和最近差异摘要，以及 `plan_state` 中的 phase 级执行进度。
- `state/snapshots/`：docx 文本快照。
- `state/diffs/`：用户审阅前后差异。
- `state/backups/`：docx 原文件备份。
- `logs/`：初始化、DOCX 写入、写作和审查日志。

## `project.json` 最小结构

- `schema_version`
- `thesis_title`
- `research_object`
- `research_scope`
- `confirmed_facts_boundary[]`
- `current_docx`
- `research_questions[]`
- `methodological_notes[]`
- `created_at`
- `updated_at`

## `terminology.json` 最小结构

- `schema_version`
- `terms[]`：统一术语及其定义或用法说明
- `abbreviations[]`：缩写及全称
- `variables[]`：变量命名及其含义
- `updated_at`

## `material_inventory.json` 最小结构

- `schema_version`
- `current_docx`
- `candidate_docx[]`
- `sources[]`
- `uncovered_questions[]`
- `deferred_sources[]`
- `coverage_notes[]`
- `updated_at`

每个 `source` 至少有：

- `source_id`
- `path`
- `title`
- `file_type`
- `role`
- `status`
- `relevance`
- `extracted_claims[]`
- `figure_ids[]`
- `table_ids[]`
- `formula_ids[]`
- `open_questions[]`
- `notes[]`

## `outline.json` 最小结构

- `schema_version`
- `main_question`
- `sections[]`
- `global_open_questions`
- `updated_at`

每个 `section` 至少有：

- `section_id`
- `title`
- `level`
- `function`
- `depends_on`
- `feeds_into`
- `status`

## `chapters/*.json` 最小结构

- `schema_version`
- `section_id`
- `title`
- `parent_id`
- `function`
- `write_goal`
- `core_question`
- `core_judgments[]`
- `dependency_inputs[]`
- `confirmed_outputs[]`
- `section_skeleton[]`
- `transition_in`
- `transition_out`
- `replan_watchpoints[]`
- `confirmed_facts`
- `forbidden_moves`
- `required_figures / required_tables / required_formulas`
- `open_questions`
- `style_notes`
- `status`
- `updated_at`

## `current_write_context.json` 最小结构

- `schema_version`
- `section_id`
- `write_goal`
- `core_judgments`
- `reasoning_mode`
- `dependency_inputs`
- `upstream_outputs`
- `confirmed_facts`
- `forbidden_moves`
- `required_evidence`
- `open_questions`
- `replan_watchpoints`
- `section_skeleton`
- `blocking_replan_items`
- `unresolved_dependencies`
- `can_write`
- `stop_reason`

## `replan_queue.json` 最小结构

- `schema_version`
- `pending[]`
- `resolved[]`
- `updated_at`

每个 item 至少有：

- `item_id`
- `source_section`
- `trigger_type`
- `reason`
- `affected_sections`
- `required_action`
- `status`

## `progress.json` 关键结构

- `schema_version`
- `completed_sections[]`
- `pending_sections[]`
- `blocked_sections[]`
- `pending_replan_items[]`
- `last_snapshot`
- `last_backup`
- `last_review_section`
- `last_review_summary`
- `last_write_context`
- `review_rounds`
- `recent_diff_summaries[]`
- `plan_state`

其中 `plan_state` 至少有：

- `current_phase`
- `resume_from`
- `last_plan_summary`
- `current_docx`
- `candidate_docx[]`
- `target_sections[]`
- `completed_phases[]`
- `material_inventory_path`
- `outline_path`
- `latest_brief_batch[]`
- `phase_status.bootstrap`
- `phase_status.inventory`
- `phase_status.outline`
- `phase_status.briefs`
- `updated_at`

## 记忆原则

- 只记录稳定、可解释、可迁移的修改偏好。
- 不把一次性润色、局部事实修正、用户个人措辞自动泛化为全局规则。
- 每轮用户审阅后先保留 diff 证据，再将真正稳定的内容写入长期记忆；证据不足的只放入暂存观察。
- 每轮 `/write` 都应优先回到 frozen plan context，而不是直接从聊天历史恢复。
- 不覆盖用户已经审定的段落。写作前先快照，写作后只对指定章节或用户授权范围操作。
- 若差异显示用户补充了事实、数据或结果，将其作为“用户提供事实”候选项，但在下一轮使用前仍需确认来源和边界。
- 若无法判断用户修改意图，向用户提问，而不是擅自总结为偏好。
- 若 write 阶段发现结构性冲突，应写入 `replan_queue.json`，而不是直接在本轮写作中偷改主线。
