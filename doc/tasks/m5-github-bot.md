# M5 — GitHub Bot 模块任务列表

> 模块职责：Webhook 事件路由、自动评审流程、`/review` 命令处理、评论创建
> 依赖：M1, M2, M4

---

## 子任务

### 5.1 事件路由

- [x] **PR-05-01** — 实现 `app/bot/event_router.py` — `EventRouter`
  - `handle_webhook(event_type, payload, signature) → WebhookResponse`
  - 流程：验证签名 → 解析事件 → 路由分发
  - PR opened/reopened/synchronize → AutoReviewHandler
  - issue_comment created → CommandHandler
  - 其他事件 → 200 忽略
- [x] **PR-05-02** — 在 `app/main.py` 注册 `POST /webhook/github` 路由
- [x] **PR-05-03** — 编写事件路由测试（各事件类型路由正确 + 签名校验失败返回 401）

### 5.2 自动评审处理器

- [x] **PR-05-04** — 实现 `app/bot/auto_review.py` — `AutoReviewHandler`
  - 构造函数注入：`github_client_factory`, `orchestrator`, `comment_creator`, `db_session_factory`
  - `handle(event)`: 完整自动评审流程
    1. 检查仓库是否开启 auto_review
    2. 创建 ReviewRecord (status=pending)
    3. 调用 M2 GitHubClient → 获取 PRDetail
    4. 调用 M4 AnalysisOrchestrator.analyze()
    5. 调用 CommentCreator 格式化评论
    6. 调用 M2 GitHubClient → 创建 PR Review（行级评论 + 总结）
    7. 更新 ReviewRecord (status=completed)
- [x] **PR-05-05** — 实现异常处理分支
  - `PRTooLargeError` → 评论提示
  - `AIProviderError` → 记录错误 + 降级提示
  - 其他异常 → 记录 + 返回 200（避免 GitHub 重试）
- [x] **PR-05-06** — 编写自动评审测试（Mock M2 + M4 → 验证完整调用链 + 异常恢复不崩溃）

### 5.3 命令处理器

- [x] **PR-05-07** — 实现 `app/bot/command_handler.py` — `CommandHandler`
  - 正则匹配 `/review` 命令（支持 `focus:security` 等参数）
  - `handle(event: IssueCommentEvent)`
    1. 正则匹配 → 非命令则忽略
    2. 权限校验 → 非协作者则评论提示
    3. 解析命令参数 → focus 类别
    4. 委托 AutoReviewHandler 执行分析
- [x] **PR-05-08** — 编写命令解析测试
  - `/review` → 全量分析
  - `/review focus:security` → 仅安全分析
  - `/review focus:security,logic` → 安全+逻辑
  - 普通评论 "looks good" → 忽略
- [x] **PR-05-09** — 编写权限校验测试（协作者可触发 + 非协作者拒绝）

### 5.4 评论创建器

- [x] **PR-05-10** — 实现 `app/bot/comment_creator.py` — `CommentCreator`
  - `build_line_comment(issue, diff_hunks) → ReviewCommentData`
    - 按 file_path + line → 定位 diff_hunk
    - severity emoji 前缀：🔴 Critical / 🟠 Warning / ⚪ Suggestion
    - Markdown 格式：问题标题 + 描述 + 修复建议 diff
  - `build_summary_comment(result, pr_url) → str`
    - Markdown 总结：变更摘要 + 问题统计表 + 高风险文件列表 + Dashboard 链接
- [x] **PR-05-11** — 实现 diff hunk 行号定位逻辑
  - 新文件行号 → diff hunk 行号映射
  - 无法定位时降级为 PR 对话评论
- [x] **PR-05-12** — 编写评论格式化测试（输入 ReviewIssue → 验证 Markdown 结构 + emoji + diff 格式）

---

## 完成标准

- [x] Webhook 事件正确路由到对应处理器
- [x] PR 自动评审全流程串联（Webhook → M2 → M4 → M2 评论）
- [x] `/review` 命令正确解析并触发分析
- [x] 非协作者无法触发 `/review`
- [x] 行级评论准确定位到 diff hunk 位置
- [x] 总结评论包含完整的问题统计
- [x] 异常不导致崩溃，返回 200 给 GitHub
