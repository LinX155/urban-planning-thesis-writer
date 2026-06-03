# 章节工件、写作上下文与 Re-Plan 工件

这个 skill 采用项目内工件驱动的工作方式，避免把长文写作的上下文只放在聊天记录里。

## 1. 全局论证图

`state/outline.json` 是 schema v2 的全局论证图。它不再只是“章节列表”，而是写清：

- 论文主问题是什么
- 有哪些 section
- 每个 section 在论证链中的功能是什么
- 哪些 section 依赖前文输出
- 哪些 section 会把结论输送给后文
- 当前哪些 section 已完成、待写、被 replan 阻塞

对长篇毕业论文来说，它承担的是“全局主线”的角色，而不是单章备忘录。

## 2. 章节 brief

每个准备进入写作的章节或小节，都应有一个 chapter brief，存放在 `state/chapters/`。

v2 brief 至少记录：

- `section_id`、标题、层级归属与章节功能
- `write_goal` 和 `core_question`
- `core_judgments`：真正准备写入正文的核心判断
- 每个 judgment 的 `reasoning_mode` 和 `evidence_anchors`
- `dependency_inputs`：它依赖哪些前文输出
- `confirmed_outputs`：它写完后能为后文提供什么
- `section_skeleton`：本节内部 3-5 个任务
- `transition_in` 与 `transition_out`
- `replan_watchpoints`
- 允许材料、confirmed facts、forbidden moves、required figures/tables/formulas、open questions、style notes

它不再只是材料清单，而是局部论证规格。

## 3. 写作上下文

每次 `/UPTW-write` 在真正开始前，都应先生成写入上下文，存放在 `state/current_write_context.json`（覆盖式，仅保留最新）。随后复制进当轮 review cycle。

写入上下文的作用不是记录所有材料，而是冻结本轮真正允许写作的 plan context。它至少要包含：

- 当前 brief 的 `write_goal`
- `core_judgments` 与 `reasoning_mode`
- `dependency_inputs`
- 上游 `confirmed_outputs`
- `required_evidence`
- `open_questions`
- `replan_watchpoints`
- 最新 review memory
- 当前 blocker：未解决依赖、pending replan item
- `can_write` / `stop_reason`

`/UPTW-write` 不应再靠”重新识别这一节要写什么”启动，而应依赖这个冻结上下文。

它是纯派生数据，始终可从 outline + chapter brief + replan_queue + memory 重新生成，因此不需要按章节归档历史版本。

## 4. Review cycle

每一轮 `/UPTW-write` 都应有一个 review cycle，存放在 `state/review-cycles/<timestamp>-<section>/`。

每个 cycle 保留：

- `request.json`：本轮写作请求、计划输入、授权范围
- `completion.json`：写作结果、plan_validation、memory_decision、快照/备份/差异路径
- `context.json`（可选）：从 `state/current_write_context.json` 复制的冻结上下文

其中：

- `request.json.plan_context` 是本轮唯一有效的计划输入
- `completion.json.plan_validation` 用来确认本轮产文是否真正满足 frozen plan
- `completion.json.memory_decision` 记录审阅后值得进入长期记忆的变更（stable_preferences、tentative_observations、rejected_generalizations、facts_confirmed、open_questions）
- 草稿内容保留在 DOCX 中，不在 cycle 目录内重复存储

## 5. Re-Plan 队列

`state/replan_queue.json` 用于保存 write 阶段发现、但不能在 write 阶段私自修复的结构性问题。

每个 replan item 至少包含：

- `item_id`
- `source_section`
- `trigger_type`
- `reason`
- `affected_sections`
- `required_action`
- `status`

触发它的典型情况是：

- 上游 `confirmed_outputs` 缺失或被推翻
- 当前证据不足以支撑某个 `core_judgment`
- 用户审阅修改使 downstream 依赖失效
- 实际写作目标与 `function / section_skeleton / transition_out` 发生结构漂移

这些问题必须回到 `/UPTW-plan` 修复，而不是在 `/UPTW-write` 里临场补丁。


