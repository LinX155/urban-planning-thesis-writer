# Plan Execution Harness

本文件只约束 `/UPTW-plan` 的执行编排，不负责定义学术写作风格。

目标是让首次 plan 在材料多、章节多、需要长程推进时，仍然保持：

- 不跳步
- 不缩水
- 不因上下文疲劳而提前收尾
- 不把“已经看过”误当成“已经深读并落盘”

## 相位定义

`/UPTW-plan` 必须按以下顺序执行：

1. `bootstrap`
2. `inventory`
3. `outline`
4. `briefs`

前一相位未完成，不得进入后一相位。

## 每个相位的最小交付

### `bootstrap`

必须完成：

- 识别 thesis project root
- 识别可用 Python
- 初始化或复用 `.urban-planning-thesis-writer/`
- 校验 state tree
- 在 `progress.json.plan_state` 中标记当前 phase 和结果

若失败：

- 立即停止
- 只报告环境或路径 blocker

### `inventory`

必须完成：

- 识别候选 thesis markdown
- 识别核心材料家族：现有论文正文、开题/中期、图表表格、实验输出、用户确认结论
- 将核心材料写入 `material_inventory.json`
- 将 thesis 题目、研究对象、研究范围、当前 markdown 等写入 `project.json`
- 从材料中提取核心术语、缩写、变量命名，写入 `terminology.json`

不得在以下情况直接推进到 `outline`：

- 有多个候选主 markdown 但未确认当前使用哪一个
- 只有“目录浏览”而没有材料级 evidence extraction
- 核心材料家族缺失且未明确记录为 blocker 或 deferred

### `outline`

必须完成：

- 冻结主问题
- 冻结 chapter/section graph
- 写清章节功能
- 写清主要依赖关系
- 写清全局 blocker 与 open questions
- 更新 `outline.json`
- 更新 `progress.json.plan_state`

### `briefs`

必须完成：

- 按用户请求覆盖的范围生成或修复 brief
- 若 brief 涉及公式，须同时登记每个公式的自然语言推导描述，确保写作阶段有对应的文字叙述依据
- 若范围很大，按批次落盘，每一批后更新 `progress.json.plan_state`
- 任何未完成部分必须写入 `resume_from`、`target_sections` 或 blocker，不得隐性丢失

## 深挖材料规则

- “读过文件名”不算 inventory 完成。
- “看过几个段落”不算 evidence extraction。
- 每份核心材料至少要留下可复用的提取结果：事实、判断、方法、图表线索、未解决问题中的一种或多种。
- 如果材料过多超出单次上下文，先把已提取部分写入 `material_inventory.json`，再继续下一批，不得为了省上下文而提前结束。
- 如果用户请求是“梳理整篇论文”，不得擅自缩成“只给一个粗框架”；应通过 batch 化 brief 和 resume 标记完成长程推进。

## 恢复规则

- 每次进入 `/UPTW-plan` 先读取 `progress.json.plan_state`。
- 若发现某个 phase 已完成，默认从下一个未完成 phase 恢复，而不是重跑全部流程。
- 若发现 `briefs` 只完成了一部分，必须从 `target_sections`、`latest_brief_batch`、`resume_from` 继续。

## 停止条件

只有以下情况允许在 phase 中途停止：

- 用户必须回答一个关键辨识问题
- 环境不可执行
- 关键材料缺失且无法安全推断

停止时必须同时落盘：

- 当前 phase
- 已完成内容
- 未完成内容
- 下一步恢复点
- blocker
