# M4 — AI 分析引擎模块任务列表

> 模块职责：AI Provider 抽象、Diff 解析、上下文构建、Prompt 模板、两阶段分析编排、结果后处理
> 依赖：M1, M3

---

## 子任务

### 4.1 AI Provider 抽象层

- [ ] **PR-04-01** — 实现 `app/engine/schemas.py` — 引擎数据结构
  - `Message`, `ChatResponse`, `Finding`, `AnalysisResult`, `AnalysisStats`, `Phase1Result`
  - `DiffHunk`, `ParsedDiff`, `AnalysisContext`
- [ ] **PR-04-02** — 实现 `app/engine/provider.py` — `AIProvider` 抽象基类
  - `chat(messages, **kwargs) → ChatResponse`
  - `get_model_name()`, `get_max_tokens()`
- [ ] **PR-04-03** — 实现 `OpenAIProvider` — OpenAI-compatible API 调用
  - 支持 `api_key`, `api_base`, `model` 参数
  - 超时 + 重试 + 异常转换（→ `AIProviderError`）
- [ ] **PR-04-04** — 编写 Provider 测试（Mock API 响应 + 错误处理 + 重试逻辑）

### 4.2 Diff 解析器

- [ ] **PR-04-05** — 实现 `app/engine/diff_parser.py` — `DiffParser`
  - `parse(pr_files: list[FileChange]) → ParsedDiff`
  - 解析 unified diff → hunks（old/new 行号映射、行内容类型）
  - `extract_changed_lines(hunk) → list[tuple[int, str]]`
  - `group_by_file(parsed) → dict[str, list[DiffHunk]]`
- [ ] **PR-04-06** — 编写 Diff 解析测试（真实 unified diff 文本 + 多文件 diff + 边界情况）

### 4.3 Prompt 模板

- [ ] **PR-04-07** — 创建 `app/engine/prompts/templates/system.j2` — 系统角色定义 + JSON 输出格式约束
- [ ] **PR-04-08** — 创建 `app/engine/prompts/templates/stage1.j2` — 阶段一变更总结模板
- [ ] **PR-04-09** — 创建 `app/engine/prompts/templates/stage2_security.j2` — 安全分析模板
- [ ] **PR-04-10** — 创建 `app/engine/prompts/templates/stage2_logic.j2` — 逻辑分析模板
- [ ] **PR-04-11** — 创建 `app/engine/prompts/templates/stage2_performance.j2` — 性能分析模板
- [ ] **PR-04-12** — 创建 `app/engine/prompts/templates/stage2_style.j2` — 代码风格 + 最佳实践模板
- [ ] **PR-04-13** — 实现 `app/engine/prompts/system.py` + `stage1.py` + `stage2.py` — Python prompt 构建函数
- [ ] **PR-04-14** — 编写 Prompt 渲染测试（验证输出包含必要字段 + JSON schema 兼容）

### 4.4 上下文构建器

- [ ] **PR-04-15** — 实现 `app/engine/context_builder.py` — `ContextBuilder`
  - `build(pr_detail, token_budget) → AnalysisContext`
  - Token 预算分配（diff 40%, AST 20%, 文件 20%, 项目 10%, 缓冲 10%）
  - 按优先级加载：diff → AST 结构 → 完整文件内容 → 项目依赖/配置
- [ ] **PR-04-16** — 编写上下文构建测试（token 预算超限时的裁剪行为）

### 4.5 后处理器

- [ ] **PR-04-17** — 实现 `app/engine/post_processor.py` — `PostProcessor`
  - 合并 AI findings + AST findings
  - 去重（同文件 + 行范围重叠 + 同 rule_id → 保留高 confidence）
  - 置信度过滤（high ≥0.6 / medium ≥0.8 / low ≥0.9）
  - 忽略规则匹配（ignore_patterns / ignore_rule_ids）
  - 启用的类别过滤
  - 排序（severity desc → confidence desc）
- [ ] **PR-04-18** — 编写后处理器测试（去重 + 阈值 + 忽略规则 + 类别过滤组合测试）

### 4.6 分析编排器

- [ ] **PR-04-19** — 实现 `app/engine/orchestrator.py` — `AnalysisOrchestrator`
  - `analyze(pr_detail) → AnalysisResult`
  - 阶段一：快速模型（provider_fast）→ 变更总结 + 高危信号 + 分析方向
  - 阶段二：强模型（provider_strong）→ 4 类并行深度分析（安全/逻辑/性能/风格）
  - 合并 + 后处理
- [ ] **PR-04-20** — 编写编排器测试（Mock Provider → 两阶段流程 → 验证阶段一输出影响阶段二输入）
- [ ] **PR-04-21** — 编写端到端 prompt 调优测试（固定 PR diff → 真实 AI API → 验证 JSON 输出格式）

---

## 完成标准

- [ ] OpenAIProvider 可成功调用 OpenAI-compatible API 并返回结构化响应
- [ ] DiffParser 正确解析 unified diff（行号映射、文件分组）
- [ ] ContextBuilder 按 token 预算正确裁剪上下文
- [ ] 所有 Prompt 模板渲染结果包含规定的 JSON 字段
- [ ] PostProcessor 正确执行去重、过滤、排序
- [ ] AnalysisOrchestrator 两阶段流程完整串联
- [ ] 真实 AI API 端到端测试返回合法 JSON（可选）
