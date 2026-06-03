# 项目级状态目录（Schema v2）

`/UPTW-init` 在用户论文项目根目录创建 `.urban-planning-thesis-writer/`。该目录用于长文协作，不应当直接展示给用户，除非用户要求查看。它既保存长期状态，也保存章节工件、写作上下文、replan 队列和每轮审阅工件。

## 目录

- `state/project.json`：论文题目、研究对象、范围、不可编造的信息边界、当前 docx。
- `state/outline.json`：schema v2 的全局论证图，含 `main_question`、`sections[]`、`global_open_questions`。
- `state/replan_queue.json`：pending / resolved 的 replan item。
- `state/chapters/*.json`：每个章节或小节的 v2 brief。
- `state/current_write_context.json`：最新一轮写作的冻结上下文（覆盖式，从信源派生）。
- `state/terminology.json`：术语、缩写、变量命名和统一称谓。
- `state/figures_formulas.json`：图、表、公式清单及正文引用状态。
- `state/memory/user_revision_preferences.json`：稳定偏好、暂存观察、已拒绝泛化项，以及最近一次审阅的章节。
- `state/memory/section_memory.json`：按章节累计的稳定偏好、暂存观察、已确认事实和待确认问题。
- `state/memory/review_history.jsonl`：每轮审阅的事件日志，含差异摘要和本轮记忆结论。
- `state/review-cycles/<timestamp>-<section>/`：每轮 `/write` 的工件目录，包含 `request.json`、`completion.json`、可选的 `context.json`。
- `state/progress.json`：已完成章节、待完成章节、blocked sections、pending replan items、最近快照、最近备份、审阅轮次和最近差异摘要。
- `state/snapshots/`：docx 文本快照。
- `state/diffs/`：用户审阅前后差异。
- `state/backups/`：docx 原文件备份。
- `logs/`：初始化、DOCX 写入、写作和审查日志。

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

## 记忆原则

- 只记录稳定、可解释、可迁移的修改偏好。
- 不把一次性润色、局部事实修正、用户个人措辞自动泛化为全局规则。
- 每轮用户审阅后先保留 diff 证据，再将真正稳定的内容写入长期记忆；证据不足的只放入暂存观察。
- 每轮 `/write` 都应优先回到 frozen plan context，而不是直接从聊天历史恢复。
- 不覆盖用户已经审定的段落。写作前先快照，写作后只对指定章节或用户授权范围操作。
- 若差异显示用户补充了事实、数据或结果，将其作为“用户提供事实”候选项，但在下一轮使用前仍需确认来源和边界。
- 若无法判断用户修改意图，向用户提问，而不是擅自总结为偏好。
- 若 write 阶段发现结构性冲突，应写入 `replan_queue.json`，而不是直接在本轮写作中偷改主线。
