# UPTW Shared Contract

UPTW 在 Codex 与 Claude Code 中都应被打包为且只应被打包为 2 个用户可见入口：

- `uptw-plan`
- `uptw-write`

不要再创建其他用户可见 skill。质量审查、图表或公式检查、反模板腔检查、一致性检查、写作上下文构建、replan 队列维护、快照、备份、记忆更新，都属于内部机制。

其中 `uptw-plan` 负责在首次进入某个论文工程时自动完成 bootstrap；初始化不再是单独的用户入口。
首次与大范围 `/UPTW-plan` 必须按 `bootstrap -> inventory -> outline -> briefs` 的内部 phase 执行，并在 phase 之间持续落盘，而不是把长流程压成一次性松散推理。

## 适用边界

- 仅在用户已经完成实验、分析、数据处理和主要结论之后使用。
- 任务目标是把现有研究材料组织成中文城市规划硕士论文 markdown。
- 不负责选题建议、研究设计、新的数据分析方法设计、结果编造、引文编造，或替用户发明结论。

## 共享硬约束

- 证据优先。现有 markdown、图表、公式、实验输出和用户确认结论高于聊天推测。
- 不得编造研究事实、数据结果、模型输出、空间发现、政策推论或来源。
- 涉及公式或计算时，必须先用自然语言叙述推导逻辑，再以公式精确化表达；变量符号按需使用，简单量优先用中文描述。
- 不得把一次性局部修改泛化成全局写作规则。
- 不得越过用户授权范围重写已审阅内容。
- 写作阶段不得静默修复结构性冲突；结构问题必须回到 plan 阶段。
- 修改 markdown 时应遵循两个原则：服从 plan/write 已冻结的授权范围、优先选择最小改动面。不要把工具层的局部保护规则误当成写作主流程本身。

## 共享工作方式

- 运行环境以 Windows 为前提，优先使用 PowerShell 和 `scripts/` 内的 Python helper。
- 需要长期状态时，工作目录是用户论文项目根目录下的 `.urban-planning-thesis-writer/`，而不是 skill 自身目录。
- 会话恢复时，优先读取项目内状态文件，而不是依赖聊天历史。
- 若关键输入缺失，提一个简洁问题，不要自行补足研究事实。
- 长程 plan 不得因为材料过多而降级成粗略浏览；若单次上下文不够，先把已提取的 inventory、outline 或 brief 批次落盘，再继续下一批。

## 项目内状态

进入任何阶段前，按需读取：

- `references/state-schema.md`
- `references/artifact-workflow.md`

恢复或续写时，优先检查：

- `.urban-planning-thesis-writer/state/progress.json`
- `.urban-planning-thesis-writer/state/replan_queue.json`
- `.urban-planning-thesis-writer/state/memory/user_revision_preferences.json`
- `.urban-planning-thesis-writer/state/memory/section_memory.json`

## 用户返回风格

- `plan`：只总结已锁定事实、章节图、当前阻塞和未决问题。
- `write`：只总结授权范围、是否允许写、完成了什么、还阻塞什么、是否更新了 markdown。
