# ReviewPilot 演示视频演讲稿

> 适用时长：8-12 分钟 | 15 张幻灯片 | 纯屏幕录制
> 按 `→` 翻页，`Home` 回首页，`End` 到末尾

---

## 开场（30 秒）— Slide 1 标题页

大家好，我是 ReviewPilot 的开发者。

ReviewPilot 是一个 AI 驱动的 GitHub PR 代码评审助手。开发者提交 PR 后，GitHub 通过 Webhook 通知后端，后端主动拉取代码变更，用 AST 确定性规则引擎 + 两阶段 AI 进行安全、逻辑、性能、风格四个维度的深度分析，最后通过 GitHub Bot 创建行级评论和总结报告，同时提供 Web Dashboard 进行跨仓库管理。

下面我为大家演示。

---

## 第一部分：问题背景（40 秒）— Slide 2 痛点

**【按 → 切换到 Slide 2】**

先说为什么要做这个项目。

代码评审是软件质量的守门员，但团队实际面临四个痛点：
- 高级开发者评审带宽有限，PR 排队成为交付瓶颈
- 新人 PR 反复修改，来回沟通消耗大量时间
- 评审标准因人而异，安全漏洞容易被遗漏
- SQL 注入、XSS、资源泄漏等隐蔽问题人工不易察觉

ReviewPilot 的解决思路很简单：用 AI 做第一轮全面初审，让人类评审者聚焦在高价值决策上。

---

## 第二部分：系统架构（60 秒）— Slide 3 架构总览

**【切换到 Slide 3 — 重点详细讲】**

系统有四个关键角色。

**第一个，GitHub**。它是事件源和展示层。开发者创建 PR 或推送代码时，GitHub 发出 Webhook POST 请求。注意，Webhook 只携带元数据——event_type、PR 编号、仓库名、installation_id——不包含任何代码。之后 Bot 的评论也贴回 GitHub PR 页面。

**第二个，ngrok**。我们的 FastAPI 服务跑在本地 127.0.0.1:8765，互联网无法直接访问。ngrok 建立一条公网隧道，把 GitHub 的 Webhook 请求转发到本地。它是一个透明的网络桥梁。

**第三个，Python 后端**。核心大脑。收到 Webhook 后验证 HMAC-SHA256 签名，解析事件类型，通过 EventRouter 路由到对应处理器。关键是：处理器跑在后台线程里，主线程立刻返回 200，避免 GitHub 的 10 秒超时。然后通过 GitHub App JWT 认证拿到 Installation Token，主动请求 GitHub API 拉取 PR 的 diff 和文件内容，再交给 AI 引擎分析。

**第四个，前端 Dashboard**。管理面板。浏览器打开 127.0.0.1:8765，GitHub OAuth 登录后查看评审历史、统计数据、仓库配置。

核心引擎是两阶段设计：Stage 1 用 deepseek-v4-flash 快速总结变更，标记风险级别和后继分析方向，目标 10 秒内完成，成本极低。Stage 2 用 deepseek-v4-pro 做四类并行深度分析——安全、逻辑、性能、风格。完成后进入后处理管道：AST findings 和 AI findings 合并 → 同文件同规则去重 → 置信度过滤 → 忽略规则匹配 → 排序输出。

---

## 第三部分：两阶段 AI 引擎（80 秒）— Slide 4 核心引擎

**【切换到 Slide 4 — 重点详细讲】**

这是 ReviewPilot 最核心的设计决策——为什么要分两个阶段？

如果用最强模型对每个 PR 做全量分析，延迟和成本都太高。一个中型 PR 几百行变更，全部用 deepseek-v4-pro 分析一次要 30-60 秒，成本也高。但全用快模型又不够深入。

所以我们把分析拆成两步。

**Stage 1** 用快模型扫一遍。输入是 PR 标题、描述、变更文件列表、diff 摘要（截断到 3000 字符）。输出四样东西：变更总结（中英文）、high-level 的风险评级（low/medium/high/critical）、分析方向建议（比如建议只关注 security 和 logic）、以及关键变更列表。

**Stage 2** 根据 Stage 1 输出的方向，用强模型做四类并行分析：

- **Security 安全**：SQL 注入、XSS、敏感信息泄露、权限绕过、不安全反序列化
- **Logic 逻辑**：空指针、边界条件、异常处理、死锁风险、状态不一致
- **Performance 性能**：N+1 查询、内存泄漏、阻塞 IO、不必要对象创建、算法复杂度
- **Style 风格**：命名规范、函数长度、圈复杂度、代码重复、最佳实践

每一类分析都是独立的 AI 调用，有自己的 prompt 模板。比如 Stage 2 的 security 分析 prompt 会包含 Phase 1 的风险摘要、完整文件内容和 AST 检测结果作为上下文。

每个 finding 都包含：rule_id、file_path、行号范围、severity、category、title、description、suggestion、confidence。

---

## 第四部分：AST 规则引擎（60 秒）— Slide 5 AST 规则

**【切换到 Slide 5 — 重点详细讲】**

除了 AI 分析，ReviewPilot 还内置了 AST 确定性规则引擎。

为什么需要 AST？因为 AI 有幻觉风险——它可能漏掉确定性的安全问题，比如 SQL 注入对 AI 来说有时会判断为"这是测试代码所以没问题"。但 AST 做的是精确语法检测。

具体实现是：用 Python 的 `ast` 模块把源码解析成抽象语法树，然后 9 个 NodeVisitor 规则依次遍历每个 AST 节点，精确匹配危险模式。

Python 共 9 条规则，按严重程度分三级：

- **Critical**（3 条）：exec/eval 动态执行、pickle 不安全反序列化、subprocess 的 shell=True 命令注入。这些是直接代码执行漏洞。
- **Warning**（5 条）：SQL 字符串拼接（检测 f-string、+、% 拼接传给 .execute() 的 SQL） 、硬编码密钥/密码（检测变量名含 password/secret/token 且赋值为字面量字符串）、裸 except（except 后面没跟异常类型）、文件操作没使用 with 语句、圈复杂度大于 15。
- **Suggestion**（1 条）：函数超过 50 行。

每条规则都有"不应触发"的测试用例。比如 ORM 的参数化查询不会被误报为 SQL 注入，测试代码中的 `test_password = "123"` 不会被报为硬编码密钥——因为 `_HardcodedSecretDetector` 会跳过这些已知测试值。

AST 做"有没有"的确定判断，AI 做"危不危险"的上下文判断，两者在 PostProcessor 中合并去重，互补输出。

---

## 第五部分：GitHub Bot 全流程（80 秒）— Slide 6 Bot 流程 + Slide 7 自动/手动

**【切换到 Slide 6 — 重点详细讲】**

好，现在看 Bot 的完整工作链路。从 PR 提交到评论出现，中间经历了 6 个步骤：

**第一步，事件接收**。开发者创建 PR、推送新代码、或重新打开 PR → GitHub 把 Webhook POST 到 ngrok 公网地址 → ngrok 转发到本地 127.0.0.1:8765/webhook/github → HMAC-SHA256 签名验证，防止伪造请求。

**第二步，事件路由**。EventRouter 解析 event_type 和 payload。如果是 pull_request 的 opened/reopened/synchronize 事件 → 交给 AutoReviewHandler。如果是 issue_comment 事件 → 交给 CommandHandler 匹配 /review 命令。关键设计：handler 在后台线程执行，主线程立刻返回 200 OK，避免 GitHub 的 10 秒超时导致重试或丢弃。

**第三步，数据拉取**。后端通过 GitHub App JWT 认证，换取 Installation Access Token，然后用这个 token 主动请求 GitHub API：get_pr 拿 PR 详情（标题、描述、author、head_sha、base_sha）；get_pr_files 拿每个变更文件的 unified diff patch；get_file_content 拿完整文件内容用于上下文构建。

**第四步，AI 分析**。就是刚讲的两阶段流程。ContextBuilder 先构建上下文（diff 占 40%、文件内容占 20%、AST 结果占 20%、项目上下文占 10%、缓冲 10%），然后依次执行 Stage 1 和 Stage 2。

**第五步，后处理**。AST findings 和 AI findings 合并 → 同文件 + 行范围重叠 + 同 rule_id → 保留高 confidence → 置信度过滤 → 忽略规则匹配 → 按 severity 降序排列。

**第六步，评论创建和持久化**。DiffParser 把 diff 文本解析成 DiffHunk 结构（包含 old_start/new_start 行号映射）。CommentCreator.build_line_comment 把每个 finding 的文件行号映射到 diff hunk 中的 position，生成行级评论精准定位到代码行。如果映射失败（问题不在变更区域），降级为 PR 对话评论。同时，ReviewRecord 和 ReviewIssue 写入 SQLite 数据库供 Dashboard 查询。

**【切换到 Slide 7 — 简要】**

除了自动触发，还支持手动命令。在 PR 评论框输入 `/review` 触发生成全量分析，`/review focus:security` 只看安全问题，`/review focus:security,logic` 看安全加逻辑。

---

## 第六部分：评论输出（30 秒）— Slide 8 评论格式

**【切换到 Slide 8 — 简要】**

输出两种格式。行级评论精准定位到代码行，红色标记 Critical 问题，附带修复建议。总结报告汇总所有 finding，列出问题统计表和高风险文件，带有 Dashboard 链接。异常情况下（比如 PR 太大超过 500KB 限制、AI API 调用失败），会降级为友好的评论提示用户，而不是崩溃——因为 GitHub 收到非 200 响应会判定投递失败并重试。

---

## 第七部分：Web Dashboard（90 秒）— Slide 9 Dashboard + Slide 10 增强视图

**【切换到 Slide 9 — 重点详细讲】**

**【切到浏览器，打开 http://127.0.0.1:8765】**

现在讲 Web Dashboard。GitHub 原生的 PR 界面只能看单个 PR 的评论，无法跨仓库查看整体的代码质量趋势。Dashboard 解决的就是这个问题。

首先 OAuth 登录。点击 "Login with GitHub" → GitHub 授权 → 回到 Dashboard。state 参数防 CSRF，session cookie 设置了 httpOnly 和 SameSite=Lax。

登录后首页展示 4 张统计卡片——总评审数、问题总数、严重问题、活跃仓库。下面是 Chart.js 渲染的环形图（严重级别分布）和柱状图（类别分布）。

`/dashboard` 页面有完整统计：问题分布、30 天趋势折线图、仓库对比柱状图。数据通过 HTMX 局部刷新，不需要整页重载。

评审记录列表支持分页和状态筛选，点进去看详情——每个 finding 的文件路径、行号、severity、修复建议。这些数据来自 ReviewIssue 表，是 AutoReviewHandler 在分析完成后逐个写入的。

**【切换到 Slide 10 — 简要】**

增强详情视图用了 Alpine.js，左侧展示代码变更、右侧按文件分组展示问题。仓库配置页支持开启/关闭自动评审、勾选检查类别、调整灵敏度、设置 glob 格式的忽略规则——每个仓库独立配置。

---

## 第八部分：误报控制（60 秒）— Slide 11 误报控制 + Slide 12 Token 预算

**【切换到 Slide 11 — 重点详细讲】**

误报控制是 ReviewPilot 区别于其他 AI review 工具的关键设计。

为什么误报比漏报伤害更大？因为企业场景下，如果 Bot 频繁给出低质量建议，评审者会产生"狼来了"效应——直接忽略所有 AI 评论，包括真正重要的安全问题。所以我们默认采取保守策略。

四层控制机制：

**第一层，置信度过滤**。三档可配：Low 灵敏度只报告 ≥90% 置信度的问题；Medium 报 ≥80%；High 报 ≥60%。默认 Medium。

**第二层，去重合并**。AST 和 AI 可能检测到同一个问题。如果同文件 + 行范围重叠 + 同 rule_id，只保留置信度更高的那个。

**第三层，忽略规则**。支持 glob 文件模式（比如跳过所有 test 文件、migrations 目录），也支持忽略特定规则 ID。

**第四层，分级报告**。Critical 必报，Warning 可选，Suggestion 默认关闭。

设计理念：保守策略建立信任 → 用户信任后自行调高灵敏度 → 形成良性循环。

**【切换到 Slide 12 — 简要】**

Token 预算管理确保 AI 拿到的是关键信息而非全部上下文。8K 预算按 40/20/20/10/10 分配，超限时按优先级裁剪。

---

## 第九部分：质量指标与扩展（40 秒）— Slide 13 质量 + Slide 14 扩展

**【切换到 Slide 13 — 简要】**

最终交付质量：126 个子任务全部完成，439 个单元测试通过，91% 代码覆盖率，mypy --strict 和 ruff check 零告警。E2E 测试使用真实 DeepSeek API 验证了两阶段模型的 JSON 输出格式。

**【切换到 Slide 14 — 简要】**

未来扩展分三步：v1.1 加通知集成和自定义规则 UI；v1.2 加反馈闭环学习和更多语言支持；v2.0 实现自动化修复和代码知识图谱。

---

## 结尾（20 秒）— Slide 15 感谢页

**【切换到 Slide 15】**

以上就是 ReviewPilot 的全部演示。从 GitHub Webhook 事件接收、ngrok 隧道转发、后台线程异步处理、GitHub API 主动拉取数据、两阶段 AI 分析、AST 确定性规则检测、DiffParser 行号映射、到行级评论和 Dashboard 管理，完整覆盖了 AI PR Review 助手的核心场景。感谢观看！

---

> ## 录制前检查清单
>
> ### 环境
> - [ ] `conda activate pytorch && cd D:\code\py\ReviewPilot`
> - [ ] `uvicorn app.main:app --host 0.0.0.0 --port 8765` 启动成功
> - [ ] `ngrok http 8765` 启动，Webhook URL 已更新
> - [ ] 浏览器访问 `http://127.0.0.1:8765/health` 返回 OK
>
> ### 浏览器标签页
> - [ ] 标签 1：`doc/demo_slides.html`（幻灯片，按 F11 全屏）
> - [ ] 标签 2：`http://127.0.0.1:8765/`（Dashboard）
> - [ ] 标签 3：GitHub 测试仓库 PR 页面
>
> ### 数据
> - [ ] 数据库中至少有 1-2 条评审记录（图表不空）
>
> ### 录制顺序
> 1. 幻灯片 S1-S5（架构介绍，约 3.5 分钟）
> 2. 切 GitHub 演示 Bot 自动评审（约 2 分钟）
> 3. 切 127.0.0.1:8765 演示 Dashboard（约 3 分钟）
> 4. 切回幻灯片 S11-S15（误报控制 + 收尾，约 2 分钟）
