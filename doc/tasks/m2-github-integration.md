# M2 — GitHub 集成模块任务列表

> 模块职责：Webhook 接收与验证、GitHub API 封装
> 依赖：M1

---

## 子任务

### 2.1 数据结构定义

- [ ] **PR-02-01** — 实现 `app/github/schemas.py`
  - `FileChange` dataclass（filename, status, patch, previous_filename）
  - `PRDetail` dataclass（pr_id, number, title, author, head_sha, base_sha, files 等）
  - `RepoStructure` dataclass（tree, config_files, dependency_files）
  - Webhook 事件 dataclass：`PROpenEvent`, `PRSyncEvent`, `IssueCommentEvent`, `UnknownEvent`

### 2.2 Webhook 处理

- [ ] **PR-02-02** — 实现 `app/github/webhook.py` — `verify_signature()` HMAC-SHA256 签名校验
- [ ] **PR-02-03** — 实现 `parse_event()` — 根据 `event_type` 解析 payload 为对应事件 dataclass
- [ ] **PR-02-04** — 实现 `extract_pr_identifiers()` — 从事件提取 (owner, repo, pr_number)
- [ ] **PR-02-05** — 编写 Webhook 测试（正确签名通过、错误签名拒绝、无签名拒绝、各事件类型解析）

### 2.3 GitHub API 客户端 — 认证

- [ ] **PR-02-06** — 实现 `app/github/client.py` — 初始化 + JWT 生成 + `get_installation_token()`
  - 通过 `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY` 生成 JWT
  - 使用 JWT 换取 installation access token
  - Token 缓存与过期处理

### 2.4 GitHub API 客户端 — 数据获取

- [ ] **PR-02-07** — 实现 `get_pr(owner, repo, pr_number)` → `PRDetail`
- [ ] **PR-02-08** — 实现 `get_pr_files(owner, repo, pr_number)` → `list[FileChange]`（含 diff patch）
- [ ] **PR-02-09** — 实现 `get_file_content(owner, repo, ref, path)` → `str`
- [ ] **PR-02-10** — 实现 `get_repo_structure(owner, repo, ref)` → `RepoStructure`（文件树 + 依赖文件 + 配置文件）

### 2.5 GitHub API 客户端 — 评论操作

- [ ] **PR-02-11** — 实现 `create_review_comment()` — 在指定 diff hunk 位置创建行级 Review Comment
- [ ] **PR-02-12** — 实现 `create_issue_comment()` — 创建 PR 对话评论
- [ ] **PR-02-13** — 实现 `create_review()` — 创建完整 PR Review（批量行级评论 + 总结）

### 2.6 GitHub API 客户端 — 辅助操作

- [ ] **PR-02-14** — 实现 `list_repo_collaborators()` — 获取仓库协作者列表（用于命令权限校验）
- [ ] **PR-02-15** — 编写 GitHubClient 方法测试（Mock PyGithub，验证参数 + 返回值）

---

## 完成标准

- [ ] Webhook HMAC-SHA256 签名校验通过/拒绝正确
- [ ] 4 种 Webhook 事件类型正确解析
- [ ] GitHubClient 可获取 PR 详情、文件 diff、文件内容、项目结构
- [ ] GitHubClient 可创建行级评论、对话评论、完整 Review
- [ ] All tests pass with mocked GitHub API
