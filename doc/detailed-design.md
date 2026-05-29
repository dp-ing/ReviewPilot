# ReviewPilot 详细设计文档

> 版本：v1.0 | 日期：2026-05-29 | 状态：待确认

---

## 1. 设计概述

### 1.1 设计目标

基于需求文档划分的 6 个子系统模块，每个模块保持**高内聚、低耦合**，通过明确的接口交互，可独立开发、独立测试、独立部署验证。

### 1.2 模块总览

```
┌──────────────────────────────────────────────────────────────────┐
│                        Web Dashboard (M6)                         │
│   Jinja2 + HTMX + Tailwind → 服务端渲染的 Web 管理界面            │
└──────────────────────────────┬───────────────────────────────────┘
                               │ REST API (内部)
┌──────────────────────────────┴───────────────────────────────────┐
│                      GitHub Bot 模块 (M5)                          │
│   PR 事件处理 · 手动命令 · 评论创建 · 分级格式化                    │
└──────────────────────────────┬───────────────────────────────────┘
                               │ 调用
┌──────────────────────────────┴───────────────────────────────────┐
│                      AI 分析引擎 (M4)                              │
│   Provider 抽象 · Diff 解析 · Prompt 构建 · 两阶段分析 · 后处理    │
└──────────────────────────────┬───────────────────────────────────┘
                               │ 调用 AST 结果
┌──────────────────────────────┴───────────────────────────────────┐
│                      AST 分析模块 (M3)                             │
│   Python AST 分析器 · Java AST 分析器 · 结果格式化                 │
└──────────────────────────────┬───────────────────────────────────┘
                               │
┌──────────────────────────────┴───────────────────────────────────┐
│                      GitHub 集成模块 (M2)                          │
│   Webhook 接收/验证 · GitHub API 封装 · 文件/PR 操作              │
└──────────────────────────────┬───────────────────────────────────┘
                               │
┌──────────────────────────────┴───────────────────────────────────┐
│                      基础设施模块 (M1)                             │
│   配置管理 · 数据库模型 · 日志 · 异常定义                           │
└──────────────────────────────────────────────────────────────────┘
```

### 1.3 模块依赖

```
M1 (基础设施)     ← 无依赖，所有模块依赖它
M2 (GitHub 集成)  ← 依赖 M1
M3 (AST 分析)     ← 依赖 M1
M4 (AI 分析引擎)  ← 依赖 M1、M3
M5 (GitHub Bot)   ← 依赖 M1、M2、M4
M6 (Web Dashboard)← 依赖 M1、M2、M5
```

---

## 2. M1 — 基础设施模块

### 2.1 职责

- 项目配置加载与校验
- 数据库模型定义与会话管理
- 结构化日志输出
- 统一异常定义

### 2.2 内部组件

#### 2.2.1 配置管理 (`app/core/config.py`)

```
Config
├── 加载 .env + 环境变量
├── 配置项（Pydantic BaseSettings）:
│   ├── GITHUB_APP_ID: str
│   ├── GITHUB_APP_PRIVATE_KEY: str
│   ├── GITHUB_WEBHOOK_SECRET: str
│   ├── AI_API_KEY: str
│   ├── AI_API_BASE: str = "https://api.openai.com/v1"
│   ├── AI_DEFAULT_MODEL: str = "gpt-4o-mini"
│   ├── AI_STRONG_MODEL: str = "gpt-4o"
│   ├── DATABASE_URL: str = "sqlite:///reviewpilot.db"
│   ├── LOG_LEVEL: str = "INFO"
│   └── APP_HOST / APP_PORT
└── 单例 get_config()
```

#### 2.2.2 数据库模型 (`app/models/`)

```
Repository
├── id: int (PK)
├── github_repo_id: int (unique)
├── full_name: str          # "owner/repo"
├── owner: str
├── config_json: Text       # JSON, 仓库级配置
├── is_active: bool
├── created_at: datetime
└── updated_at: datetime

PullRequest
├── id: int (PK)
├── repository_id: int (FK → Repository)
├── github_pr_id: int
├── number: int
├── title: str
├── author: str
├── branch: str
├── base_branch: str
├── status: str             # open/closed/merged
├── created_at: datetime
└── updated_at: datetime

ReviewRecord
├── id: int (PK)
├── pull_request_id: int (FK → PullRequest)
├── trigger: str            # auto / manual
├── commit_sha: str
├── summary: str            # AI 生成的变更总结
├── issue_count: int
├── critical_count: int
├── warning_count: int
├── suggestion_count: int
├── status: str             # pending/completed/failed
├── started_at: datetime
├── completed_at: datetime
└── error_message: str?

ReviewIssue
├── id: int (PK)
├── review_record_id: int (FK → ReviewRecord)
├── file_path: str
├── line_start: int?
├── line_end: int?
├── severity: str           # critical/warning/suggestion
├── category: str           # security/logic/performance/best_practice/style
├── rule_id: str            # 规则标识, 如 "python-sql-injection"
├── title: str
├── description: str
├── suggestion: str?
├── suggestion_diff: str?   # 修复建议的 diff 格式
├── confidence: float?      # AI 置信度, 0-1
├── status: str             # open/confirmed/ignored
├── github_comment_id: int? # GitHub review comment ID
└── created_at: datetime

User
├── id: int (PK)
├── github_user_id: int (unique)
├── login: str
├── avatar_url: str?
├── role: str               # admin / member
├── created_at: datetime
└── last_login_at: datetime

RepoConfig
├── id: int (PK)
├── repository_id: int (FK → Repository, unique)
├── auto_review: bool       # 是否开启自动评审
├── sensitivity: str        # high / medium / low
├── enabled_categories: str # JSON array, 启用的检查类别
├── ignore_patterns: str    # JSON array, 忽略的文件模式
├── ignore_rule_ids: str    # JSON array, 忽略的规则ID
├── language: str           # zh / en, 输出语言
└── updated_at: datetime
```

#### 2.2.3 日志 (`app/core/logging.py`)

- 基于 Python `logging` + `structlog`
- 统一 JSON 格式输出
- 不记录完整的源代码内容（安全要求）
- 日志级别通过 `LOG_LEVEL` 配置

#### 2.2.4 异常定义 (`app/core/exceptions.py`)

```
ReviewPilotException (base)
├── ConfigError             # 配置错误
├── GitHubAPIError          # GitHub API 调用失败
├── WebhookVerifyError      # Webhook 签名校验失败
├── AIProviderError         # AI API 调用失败
├── AnalysisError           # 分析过程错误
├── PRTooLargeError         # PR 过大无法分析
├── ASTParseError           # AST 解析失败
├── NotFoundError           # 资源不存在
└── PermissionDeniedError   # 权限不足
```

### 2.3 对外接口

| 接口 | 说明 |
|------|------|
| `get_config()` | 获取全局配置单例 |
| `get_db_session()` | 获取数据库会话（依赖注入） |
| `get_logger(name)` | 获取结构化日志实例 |
| 异常类 | 各模块捕获并重新抛出 |

### 2.4 测试策略

- 配置加载测试：各配置项默认值、环境变量覆盖
- 数据库模型测试：CRUD 操作、关系查询、JSON 字段序列化
- 异常测试：各异常类的构造与继承关系

---

## 3. M2 — GitHub 集成模块

### 3.1 职责

- 接收并验证 GitHub Webhook 请求
- 封装 GitHub REST API 调用（PR、文件、评论操作）
- 提供统一的认证 token 管理

### 3.2 内部组件

#### 3.2.1 Webhook 处理器 (`app/github/webhook.py`)

```
WebhookHandler
├── verify_signature(payload, signature) → bool
│   使用 HMAC-SHA256 + GITHUB_WEBHOOK_SECRET 校验
│
├── parse_event(event_type, payload) → WebhookEvent
│   └── 返回类型:
│       ├── PROpenEvent(pr_id, repo_full_name, ...)
│       ├── PRSyncEvent(pr_id, repo_full_name, commit_sha, ...)
│       ├── IssueCommentEvent(pr_id, repo_full_name, body, ...)
│       └── UnknownEvent
│
└── extract_pr_identifiers(event) → (owner, repo, pr_number)
```

#### 3.2.2 GitHub API 客户端 (`app/github/client.py`)

```
GitHubClient (基于 PyGithub 封装)
├── get_pr(owner, repo, pr_number) → PRDetail
├── get_pr_files(owner, repo, pr_number) → list[FileChange]
├── get_file_content(owner, repo, ref, path) → str
├── get_repo_structure(owner, repo, ref) → RepoStructure
│   获取项目结构: 文件树、配置文件、依赖声明
│
├── create_review_comment(pr, body, commit_id, path, line, side) → comment_id
│   创建行级 Review Comment
├── create_issue_comment(pr, body) → comment_id
│   创建 PR 对话评论（总结用）
├── create_review(pr, comments, body) → review_id
│   创建完整的 PR Review（包含多条行级评论 + 总结）
│
├── list_repo_collaborators(owner, repo) → list[Collaborator]
│   用于命令权限校验
│
└── get_installation_token(installation_id) → str
    通过 GitHub App 获取 token
```

**GitHubClient 实例化时需要：**
- `installation_id`（来自 Webhook 事件）
- 内部通过 `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY` 生成 JWT

#### 3.2.3 数据结构

```python
@dataclass
class FileChange:
    filename: str
    status: str              # added/modified/removed/renamed
    patch: str               # unified diff 文本
    previous_filename: str?  # 重命名时

@dataclass
class PRDetail:
    pr_id: int
    number: int
    title: str
    body: str?
    author: str
    head_sha: str
    base_sha: str
    head_branch: str
    base_branch: str
    files: list[FileChange]
    diff_url: str

@dataclass
class RepoStructure:
    tree: list[str]           # 文件路径列表
    config_files: dict        # {文件名: 内容}, 如 setup.py, pom.xml, package.json
    dependency_files: dict    # {文件名: 内容}, 如 requirements.txt
```

### 3.3 对外接口

| 接口 | 说明 |
|------|------|
| `WebhookHandler.verify_signature()` | M5 调用，验证请求合法性 |
| `WebhookHandler.parse_event()` | M5 调用，解析事件类型 |
| `GitHubClient` 的全部公共方法 | M5、M6 调用，执行 GitHub 操作 |

### 3.4 测试策略

- Webhook 签名校验测试：正确签名通过、错误签名拒绝、无签名单拒绝
- Webhook 事件解析测试：各事件类型 JSON 的正确解析
- GitHub API Mock 测试：使用 Mock 验证方法调用参数正确性
- 集成测试（可选）：使用 GitHub 的测试仓库验证真实 API 调用

---

## 4. M3 — AST 分析模块

### 4.1 职责

- 对 Python 代码进行 AST 解析，执行确定性规则检查
- 对 Java 代码进行 AST 解析，执行确定性规则检查
- 提取代码结构信息（函数边界、变量作用域、调用关系）
- 将 AST 分析结果格式化为标准化输出，供 M4 作为增强上下文使用

### 4.2 设计原则

AST 模块**不依赖 AI**，结果是确定性的（相同输入 → 相同输出）。这保证：
- 可独立测试（给定代码片段，断言输出问题列表）
- 不消耗 AI token
- 可作为 AI 分析的增强输入

### 4.3 内部组件

#### 4.3.1 分析器抽象基类 (`app/analyzer/ast_base.py`)

```python
class ASTAnalyzer(ABC):
    """AST 分析器基类"""

    @abstractmethod
    def get_supported_language(self) -> str:
        """返回支持的语言标识: 'python' / 'java'"""
        ...

    @abstractmethod
    def analyze_file(self, filename: str, source: str) -> ASTResult:
        """分析单个文件的源代码"""
        ...

    @abstractmethod
    def extract_structure(self, filename: str, source: str) -> CodeStructure:
        """提取代码结构信息（函数、类、import 等）"""
        ...
```

#### 4.3.2 Python AST 分析器 (`app/analyzer/python_analyzer.py`)

```
PythonAnalyzer (extends ASTAnalyzer)
├── 使用 Python 标准库 ast 模块
│
├── 确定性规则检查:
│   ├── [Critical] exec() / eval() 调用          → rule: python-exec-eval
│   ├── [Critical] pickle.loads() 不受信数据     → rule: python-unsafe-pickle
│   ├── [Critical] subprocess shell=True         → rule: python-shell-injection
│   ├── [Warning] SQL 字符串拼接                 → rule: python-sql-concat
│   ├── [Warning] 裸 except: 捕获所有异常       → rule: python-bare-except
│   ├── [Warning] 硬编码密码/密钥               → rule: python-hardcoded-secret
│   ├── [Warning] 文件操作缺少 with 语句        → rule: python-file-leak
│   ├── [Warning] 函数圈复杂度 > 15             → rule: python-complexity
│   ├── [Suggestion] 函数长度 > 50 行           → rule: python-function-length
│   └── [Suggestion] 重复代码块识别             → rule: python-duplicate
│
└── 结构提取:
    ├── 函数/方法列表（名称、起止行号、参数）
    ├── 类定义列表（名称、基类、方法列表）
    ├── import 语句列表
    ├── 顶层变量赋值
    └── 异常处理块（try/except/finally）
```

#### 4.3.3 Java AST 分析器 (`app/analyzer/java_analyzer.py`)

```
JavaAnalyzer (extends ASTAnalyzer)
├── 使用 javalang 库解析 Java 代码
│
├── 确定性规则检查:
│   ├── [Critical] Runtime.exec() 调用           → rule: java-command-injection
│   ├── [Critical] 不安全的反序列化               → rule: java-unsafe-deserial
│   ├── [Warning] Statement 拼接 SQL             → rule: java-sql-concat
│   ├── [Warning] 资源未在 try-with-resources 中 → rule: java-resource-leak
│   ├── [Warning] 硬编码密码/密钥                 → rule: java-hardcoded-secret
│   ├── [Warning] 方法圈复杂度 > 15              → rule: java-complexity
│   ├── [Suggestion] 方法长度 > 50 行            → rule: java-method-length
│   └── [Suggestion] 未处理的异常抛出            → rule: java-unhandled-exception
│
└── 结构提取:
    ├── 方法列表（名称、起止行号、参数、返回类型、异常）
    ├── 类定义列表（包名、类名、基类、接口）
    ├── import 语句列表
    └── 注解列表
```

#### 4.3.4 分析器注册表 (`app/analyzer/registry.py`)

```python
class AnalyzerRegistry:
    """按语言获取对应的分析器"""

    def __init__(self):
        self._analyzers: dict[str, ASTAnalyzer] = {}

    def register(self, analyzer: ASTAnalyzer) -> None: ...
    def get(self, language: str) -> ASTAnalyzer | None: ...
    def detect_language(self, filename: str) -> str | None: ...
```

在应用启动时注册 `PythonAnalyzer` 和 `JavaAnalyzer`。

#### 4.3.5 输出数据结构

```python
@dataclass
class ASTFinding:
    rule_id: str
    severity: str            # critical/warning/suggestion
    category: str            # security/logic/performance/best_practice/style
    file_path: str
    line_start: int
    line_end: int
    title: str
    description: str
    code_snippet: str        # 触发问题的代码片段

@dataclass
class CodeStructure:
    language: str
    functions: list[FunctionInfo]   # 名称、起止行号、参数列表
    classes: list[ClassInfo]        # 名称、继承关系、方法列表
    imports: list[str]
    calls: list[CallInfo]           # 被调用的函数/方法列表

@dataclass
class ASTResult:
    findings: list[ASTFinding]
    structure: CodeStructure
```

### 4.4 对外接口

| 接口 | 说明 |
|------|------|
| `AnalyzerRegistry.get(language)` | M4 调用，获取分析器 |
| `ASTAnalyzer.analyze_file()` | M4 调用，执行确定性规则检查 |
| `ASTAnalyzer.extract_structure()` | M4 调用，提取代码结构 |

### 4.5 测试策略

- **规则级别测试**：每个规则独立测试，给定触发代码 → 断言产生问题；给定正常代码 → 断言无问题
- **分析器级别测试**：对完整 Python/Java 文件进行扫描，验证多规则并行执行
- **结构提取测试**：验证提取的函数、类、import 数量正确
- **误报控制测试**：常见非问题模式（如 SQL 构建器库的使用）不应触发规则

---

## 5. M4 — AI 分析引擎

### 5.1 职责

- 封装 AI 模型调用（Provider 抽象层）
- 解析 PR diff 并构建分析上下文
- 执行两阶段 AI 分析流程
- 后处理 AI 输出为标准化的 `ReviewIssue` 列表

### 5.2 核心流程

```
┌────────────────────┐
│  M5 Bot 调用入口    │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ 1. Diff 解析        │  解析 unified diff → 变更文件列表 + diff_hunk 定位
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ 2. 上下文构建       │  获取文件内容 + 项目结构 + AST 结果
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ 3. 阶段一：总结    │  快速模型, 低 token → 变更总结 + 高危信号标记
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ 4. 阶段二：深度    │  强模型, 并行 ≤3 个 chunk → 详细问题发现 + 修复建议
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ 5. 结果后处理       │  合并 → 去重 → 置信度过滤 → 分级 → 格式化
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ 返回标准化结果      │  → M5 Bot 创建评论
└────────────────────┘
```

### 5.3 内部组件

#### 5.3.1 AI Provider 抽象层 (`app/engine/provider.py`)

```python
class AIProvider(ABC):
    """AI 模型 Provider 抽象基类"""

    @abstractmethod
    def chat(self, messages: list[Message], **kwargs) -> ChatResponse:
        """发送 chat completion 请求"""
        ...

    @abstractmethod
    def get_model_name(self) -> str: ...

    @abstractmethod
    def get_max_tokens(self) -> int: ...

class OpenAIProvider(AIProvider):
    """OpenAI / DeepSeek / 其他兼容接口的 Provider"""
    def __init__(self, api_key, api_base, model): ...
    def chat(self, messages, **kwargs) -> ChatResponse: ...

# 通过配置创建实例:
#   provider_fast = OpenAIProvider(key, base, config.AI_DEFAULT_MODEL)
#   provider_strong = OpenAIProvider(key, base, config.AI_STRONG_MODEL)
```

Provider 的接口只暴露 `chat()`，不关心具体厂商实现。后续添加 Anthropic 等 Provider 只需实现同一接口。

#### 5.3.2 Diff 解析器 (`app/engine/diff_parser.py`)

```python
@dataclass
class DiffHunk:
    """单个 diff 块"""
    file_path: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    header: str              # @@ 头部
    lines: list[tuple[str, str]]  # [(type: +/-, content)]

@dataclass
class ParsedDiff:
    """解析后的完整 diff"""
    files: list[str]         # 变更文件列表
    hunks: list[DiffHunk]    # 所有 diff 块
    total_additions: int
    total_deletions: int
    raw_diff: str            # 原始 diff 文本

class DiffParser:
    def parse(self, pr_files: list[FileChange]) -> ParsedDiff: ...
    def extract_changed_lines(self, hunk: DiffHunk) -> list[tuple[int, str]]: ...
    def group_by_file(self, parsed: ParsedDiff) -> dict[str, list[DiffHunk]]: ...
```

#### 5.3.3 上下文构建器 (`app/engine/context_builder.py`)

```python
@dataclass
class AnalysisContext:
    """分析上下文"""
    pr_info: dict               # PR 标题、描述、分支信息
    diff: ParsedDiff
    file_contents: dict[str, str]       # {文件路径: 完整内容}  按需获取
    ast_results: dict[str, ASTResult]   # {文件路径: AST 结果}  M3 提供
    project_structure: RepoStructure     # 项目结构               M2 提供
    token_budget: int                   # 可用 token 总量

class ContextBuilder:
    def __init__(self, github_client: GitHubClient, analyzer_registry: AnalyzerRegistry):
        ...

    def build(
        self,
        pr_detail: PRDetail,
        token_budget: int = DEFAULT_TOKEN_BUDGET
    ) -> AnalysisContext:
        """
        构建分析上下文:
        1. 解析 diff → ParsedDiff
        2. 计算 diff token 数 → 预留阶段二空间
        3. 按 token 预算获取增强上下文:
           - 优先: 变更文件的 AST 结构提取
           - 其次: 变更文件的完整内容
           - 最后: 项目依赖/配置文件
        4. 运行 M3 确定性规则检查 → ast_results
        5. 组装 AnalysisContext
        """
        ...
```

**Token 预算分配策略：**

| 组件 | 比例 | 说明 |
|------|------|------|
| Diff | 40% | 核心信息，不可压缩 |
| AST 结果 + 代码结构 | 20% | M3 输出，增强分析精度 |
| 完整文件内容 | 20% | 优先取变更行 ±50 行 |
| 项目上下文 | 10% | 依赖信息、配置文件 |
| 缓冲 | 10% | 实际分析时可能有波动 |

#### 5.3.4 Prompt 模板 (`app/engine/prompts/`)

```
prompts/
├── system_prompt.py         # 系统 prompt: 评审角色定义、输出格式约束
├── stage1_summary.py        # 阶段一: 变更总结 prompt
├── stage2_security.py       # 阶段二-1: 安全分析 prompt
├── stage2_logic.py          # 阶段二-2: 逻辑分析 prompt
├── stage2_performance.py    # 阶段二-3: 性能分析 prompt
├── stage2_style.py          # 阶段二-4: 代码风格+最佳实践 prompt
└── templates/               # Jinja2 模板
    ├── system.j2
    ├── stage1.j2
    └── stage2_*.j2

AI 输出格式约束（所有 prompt 要求返回 JSON）:
{
  "findings": [
    {
      "file_path": "src/app.py",
      "line_start": 42,
      "line_end": 45,
      "severity": "warning",           // critical/warning/suggestion
      "category": "security",          // security/logic/performance/best_practice/style
      "title": "SQL 注入风险",
      "description": "用户输入直接拼接到 SQL 查询中...",
      "suggestion": "使用参数化查询替代字符串拼接: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
      "suggestion_diff": "- cursor.execute(f'SELECT * FROM users WHERE id = {user_id}')\n+ cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
      "confidence": 0.92
    }
  ],
  "summary": "本次 PR 新增了用户查询接口..."
}
```

#### 5.3.5 分析编排器 (`app/engine/orchestrator.py`)

```python
class AnalysisOrchestrator:
    """两阶段分析编排器"""

    def __init__(
        self,
        provider_fast: AIProvider,      # 阶段一用快速模型
        provider_strong: AIProvider,    # 阶段二用强模型
        diff_parser: DiffParser,
        context_builder: ContextBuilder,
    ): ...

    async def analyze(self, pr_detail: PRDetail) -> AnalysisResult:
        """
        1. 构建上下文 (ContextBuilder)
        2. 阶段一: 快速总结 + 高危信号标记
           - 使用 provider_fast (gpt-4o-mini)
           - 输入: PR 信息 + diff 文本 + AST 规则检查结果
           - 输出: 变更总结 + 高危文件标记 + 分析方向建议
        3. 阶段二: 深度分析（并行）
           - 使用 provider_strong (gpt-4o)
           - 按类别并行调用:
             ├── analyze_security(context, phase1_hints)
             ├── analyze_logic(context, phase1_hints)
             ├── analyze_performance(context, phase1_hints)
             └── analyze_style(context, phase1_hints)
           - 每类返回 findings 列表
        4. 合并 + 后处理 → AnalysisResult
        """
        ...

    async def _phase1_summary(self, ctx: AnalysisContext) -> Phase1Result:
        """阶段一: 调用快速模型做总结"""
        ...

    async def _phase2_deep_analysis(self, ctx: AnalysisContext, hints: Phase1Result) -> list[Finding]:
        """阶段二: 4 类并行深度分析"""
        ...

class AnalysisResult:
    summary: str              # 中文/英文 变更总结
    findings: list[Finding]   # 所有发现
    stats: AnalysisStats      # 问题统计

class AnalysisStats:
    total: int
    critical: int
    warning: int
    suggestion: int
    by_category: dict[str, int]
    high_risk_files: list[str]
```

#### 5.3.6 后处理器 (`app/engine/post_processor.py`)

```python
class PostProcessor:
    """分析结果后处理"""

    def __init__(self, repo_config: RepoConfig): ...

    def process(self, raw_findings: list[Finding], ast_findings: list[ASTFinding]) -> list[ReviewIssue]:
        """
        1. 合并 AI 结果 + AST 结果（两者兼有模式）
        2. 去重: 同一文件+同一行+同类型问题合并（AI 和 AST 可能发现同一问题）
        3. 置信度过滤:
           - sensitivity=high:  报告 ≥ 0.6
           - sensitivity=medium: 报告 ≥ 0.8
           - sensitivity=low:    报告 ≥ 0.9
        4. 忽略规则过滤: 匹配 ignore_patterns / ignore_rule_ids
        5. 应用启用的类别: 过滤 disabled categories
        6. 排序: severity desc → confidence desc
        7. 转换为 ReviewIssue 模型
        """
        ...
```

**去重策略：**
- 同一文件 + 行范围重叠 + 同一 `rule_id` → 保留 confidence 高的
- 同一文件 + 行范围重叠 + 不同 `rule_id` → 都保留（不同角度的问题）

### 5.4 对外接口

| 接口 | 说明 |
|------|------|
| `AnalysisOrchestrator.analyze(pr_detail) → AnalysisResult` | M5 调用，完整的 AI 分析流程 |

### 5.5 测试策略

- **Provider 层**：Mock AI API 响应，测试 chat() 方法参数构造、错误处理、超时重试
- **Diff 解析器**：用真实 unified diff 文本测试，验证 hunk 行号映射、文件分组
- **上下文构建器**：测试 token 预算分配逻辑（给定限制，验证只加载应有上下文）
- **Prompt 模板**：渲染结果包含必要字段、JSON schema 兼容
- **后处理器**：去重、过滤、阈值、忽略规则的组合测试
- **编排器**：Mock Provider → 测试两阶段流程 → 验证阶段一输出影响阶段二输入
- **集成测试**：对固定 PR diff 文本 → 用真实 AI API → 验证输出 JSON 格式（非功能性，仅用于 prompt 调优）

---

## 6. M5 — GitHub Bot 模块

### 6.1 职责

- 接收 Webhook 事件，路由到对应处理器
- 编排 PR 自动评审流程（M2 → M3 → M4 → M2 评论）
- 处理手动 `/review` 命令
- 创建行级评论和总结评论

### 6.2 处理流程

#### 6.2.1 自动评审流程

```
Webhook (opened/reopened/synchronize)
  │
  ▼
M5 事件路由 (event_router.py)
  │
  ├── 检查仓库配置: auto_review 是否开启?
  │   └── 否 → 忽略，返回 200
  │
  ├── 创建 ReviewRecord (status=pending)
  │
  ├── 调用 M2 GitHubClient → 获取 PR Detail
  │
  ├── 调用 M4 AnalysisOrchestrator.analyze()
  │
  ├── 调用 M2 GitHubClient → 创建 PR Review
  │   ├── create_review(body=summary, comments=line_comments)
  │   └── 每个 finding 定位到对应的 diff_hunk
  │
  ├── 更新 ReviewRecord (status=completed, issue_count=...)
  │
  └── 异常处理:
      ├── PRTooLargeError → 评论提示 PR 过大
      ├── AIProviderError → 记录错误，降级提示
      └── 其他异常 → 记录, 返回 200 (避免 GitHub 重试)
```

#### 6.2.2 手动命令流程

```
Webhook (issue_comment created)
  │
  ▼
M5 事件路由
  │
  ├── 解析评论 body, 匹配 /review 命令
  │   └── 非命令 → 忽略
  │
  ├── 权限校验: GitHubClient.list_repo_collaborators()
  │   └── 非协作者 → 评论提示无权限
  │
  ├── 解析命令参数:
  │   /review → 默认全量分析
  │   /review focus:security → 仅安全分析
  │
  ├── 后续流程同自动评审
  │
  └── 额外: 在分析完成后 Reply 通知触发者
```

### 6.3 内部组件

#### 6.3.1 事件路由 (`app/bot/event_router.py`)

```python
class EventRouter:
    """Webhook 事件路由"""

    def __init__(
        self,
        webhook_handler: WebhookHandler,       # M2
        auto_review_handler: AutoReviewHandler,
        command_handler: CommandHandler,
    ): ...

    async def handle_webhook(
        self, event_type: str, payload: dict, signature: str
    ) -> WebhookResponse:
        """
        1. verify_signature(signature)
        2. parse_event(event_type, payload)
        3. 路由:
           - PR opened/reopened/synchronize → auto_review_handler.handle()
           - issue_comment created → command_handler.handle()
           - 其他事件 → 200 OK (忽略)
        """
        ...
```

#### 6.3.2 自动评审处理器 (`app/bot/auto_review.py`)

```python
class AutoReviewHandler:
    def __init__(
        self,
        github_client_factory: Callable[[int], GitHubClient],  # installation_id → client
        orchestrator: AnalysisOrchestrator,                      # M4
        comment_creator: CommentCreator,
        db_session_factory,
    ): ...

    async def handle(self, event: PRSyncEvent) -> None:
        """
        完整自动评审流程（6.2.1）
        """
        ...
```

#### 6.3.3 命令处理器 (`app/bot/command_handler.py`)

```python
class CommandHandler:
    """处理 /review 命令"""

    COMMAND_PATTERN = re.compile(r'^/review(?:\s+focus:(\w+(?:,\w+)*))?')

    def __init__(self, auto_review_handler: AutoReviewHandler): ...

    async def handle(self, event: IssueCommentEvent) -> None:
        """
        1. 正则匹配 /review 命令
        2. 解析参数（focus:security,logic 等）
        3. 权限校验
        4. 委托 auto_review_handler.handle() 执行分析
        """
        ...
```

#### 6.3.4 评论创建器 (`app/bot/comment_creator.py`)

```python
class CommentCreator:
    """创建格式化的 PR 评论"""

    def __init__(self, github_client: GitHubClient): ...

    def build_line_comment(self, issue: ReviewIssue, diff_hunks: list[DiffHunk]) -> ReviewCommentData:
        """
        将 ReviewIssue 转换为 GitHub Review Comment 参数:
        - 根据 file_path + line 定位到对应的 diff_hunk
        - 按 severity 添加 emoji 前缀: 🔴 Critical / 🟠 Warning / ⚪ Suggestion
        - 格式:
          **{severity_label}**: {title}
          {description}
          **建议修复**:
          ```suggestion
          {suggestion_diff}
          ```
        """
        ...

    def build_summary_comment(self, result: AnalysisResult, pr_url: str) -> str:
        """
        构建总结评论 (Markdown):
        ## 🤖 AI Review 总结
        {summary}

        ### 问题统计
        | 级别 | 数量 |
        |------|------|
        | Critical | {n} |
        | Warning | {m} |
        | Suggestion | {k} |

        ### 高风险文件
        {file_list}

        ---
        > 查看完整分析报告: {dashboard_url}
        """
        ...
```

### 6.4 对外接口

| 接口 | 说明 |
|------|------|
| `EventRouter.handle_webhook()` | FastAPI 路由 `/webhook/github` 调用 |
| `CommentCreator.build_*()` | M6 也可能调用（Web 端手动触发评审时复用） |

### 6.5 测试策略

- **事件路由测试**：各事件类型路由正确性、签名校验失败返回 401
- **自动评审**：Mock M2 + M4 → 验证完整流程调用了正确的依赖方法
- **命令解析**：测试 `/review`、`/review focus:security`、普通评论（忽略）
- **评论格式化**：输入 ReviewIssue 列表 → 验证输出 Markdown 结构
- **权限校验**：协作者可触发、非协作者拒绝
- **异常恢复**：M4 抛出异常时 → 不崩溃、记录错误、返回 200

---

## 7. M6 — Web Dashboard 模块

### 7.1 职责

- GitHub OAuth 用户认证
- 评审记录列表与详情展示
- 多仓库统计概览与趋势图
- 仓库评审配置管理
- PR 增强详情视图（diff + 问题标注）

### 7.2 技术方案

- **渲染**：Jinja2 服务端渲染页面 + HTMX 处理局部刷新和异步加载
- **样式**：Tailwind CSS（CDN 或构建）
- **图表**：Chart.js（CDN，轻量）
- **认证**：GitHub OAuth + session cookie

### 7.3 内部组件

#### 7.3.1 认证模块 (`app/web/auth.py`)

```
GitHub OAuth 流程:
1. GET /auth/login → 重定向到 GitHub OAuth 授权页
2. 用户授权后回调 → GET /auth/callback?code=xxx
3. 用 code 换 access_token → 获取用户信息
4. 匹配/创建 User 记录
5. 设置 session cookie
6. 重定向到 Dashboard 首页

Auth middleware:
- 从 session 读取 user_id → 查询 User → 注入 request.state.user
- 未登录用户访问非公开路由 → 重定向到 /auth/login
- 仓库权限校验: 检查用户是否有权访问该仓库的数据
```

#### 7.3.2 页面路由与模板 (`app/web/routes.py`)

```
路由规划（全部返回 HTML 页面）:

主页 & 认证
├── GET  /                    → 首页（未登录→登录页, 已登录→Dashboard）
├── GET  /auth/login          → GitHub OAuth 重定向
└── GET  /auth/callback       → OAuth 回调处理

Dashboard
├── GET  /dashboard           → 统计概览（仓库列表 + 图表）
└── GET  /dashboard/stats     → HTMX 局部刷新统计数据 JSON/HTML

评审记录
├── GET  /reviews             → 评审记录列表（支持筛选: 仓库/状态/时间）
├── GET  /reviews/{id}        → 评审详情（问题列表 + 代码上下文）
└── PATCH /api/reviews/{id}/issues/{issue_id} → HTMX 更新问题状态

配置管理
├── GET  /repositories        → 仓库配置列表
├── GET  /repositories/{id}/config → 仓库配置编辑页
└── PUT  /api/repositories/{id}/config → 保存配置（HTMX）

增强详情
└── GET  /reviews/{id}/enhanced → PR 增强详情（diff + 问题标注）
```

#### 7.3.3 模板结构 (`app/templates/`)

```
templates/
├── base.html                # 基础布局 (header + sidebar + content)
├── index.html               # 首页（未登录引导）
├── auth/
│   └── login_prompt.html    # 登录引导页
├── dashboard/
│   ├── overview.html        # Dashboard 主页（统计卡片 + 图表）
│   ├── stats_cards.html     # HTMX 局部: 统计数字
│   └── trend_chart.html     # HTMX 局部: 趋势图
├── reviews/
│   ├── list.html            # 评审记录列表
│   ├── detail.html          # 评审详情
│   ├── issue_row.html       # HTMX 局部: 单条 issue 行
│   └── enhanced.html        # 增强详情视图（diff + 标注）
├── repos/
│   ├── list.html            # 仓库列表
│   ├── config.html          # 配置编辑页
│   └── config_form.html     # HTMX 局部: 配置表单
└── shared/
    ├── severity_badge.html  # 严重级别标签组件
    ├── pagination.html      # 分页组件
    └── filter_bar.html      # 筛选栏组件
```

#### 7.3.4 统计服务 (`app/web/stats_service.py`)

```python
class StatsService:
    """Dashboard 统计查询服务"""

    def get_overview_stats(self, repo_ids: list[int] = None) -> OverviewStats:
        """
        - 总 PR 数
        - 总评审数
        - 总问题数
        - 平均问题数/PR
        - 本期新增问题数
        """

    def get_issue_distribution(self, repo_id: int, days: int = 30) -> IssueDistribution:
        """
        按严重级别: {critical: n, warning: n, suggestion: n}
        按类别: {security: n, logic: n, ...}
        """

    def get_trend(self, repo_id: int, days: int = 30) -> list[TrendPoint]:
        """
        每日问题发现数 / 每日评审数
        """

    def get_repo_comparison(self) -> list[RepoStats]:
        """各仓库对比"""
```

#### 7.3.5 增强详情视图 (`app/web/enhanced_view.py`)

```python
class EnhancedViewBuilder:
    """构建 PR 增强详情页面"""

    def build(
        self,
        review_record: ReviewRecord,
        pr_detail: PRDetail,          # 通过 M2 获取
        issues: list[ReviewIssue],
    ) -> EnhancedViewData:
        """
        1. 获取 PR 的完整 file diff
        2. 将 issues 按文件分组、按行排序
        3. 构建 diff 行与 issue 的映射
        4. 渲染: diff 侧 + 问题标注侧
           - 代码行高亮: added(绿) / removed(红)
           - 问题行左侧标记 severity 颜色条
           - 点击标记展开 issue 详情
        """
        ...
```

### 7.4 对外接口

| 接口 | 说明 |
|------|------|
| HTTP 路由 | 所有页面和 API 端点 |
| `POST /webhook/github` | GitHub Webhook 接收（M5 处理） |

### 7.5 测试策略

- **认证测试**：未登录重定向、登录后 session 正确、回调处理 code 交换
- **页面渲染测试**：各路由返回 200、模板变量正确填充
- **HTMX 交互测试**：局部刷新端点返回正确的 HTML fragment
- **统计查询测试**：Mock 数据库数据 → 验证统计数字正确
- **增强视图测试**：diff + issue 映射的正确性

---

## 8. 模块间数据流

### 8.1 PR 自动评审（主流程）

```
1. GitHub → POST /webhook/github → M5 (EventRouter)
2. M5 → verify_signature → M2 (WebhookHandler)
3. M5 → parse_event → M2 (WebhookHandler) → 得到 PRSyncEvent
4. M5 → 查询 RepoConfig → M1 (数据库)
5. M5 → get_pr / get_pr_files → M2 (GitHubClient) → PRDetail
6. M5 → analyze(PRDetail) → M4 (AnalysisOrchestrator)
  6a. M4 → 解析 diff → DiffParser
  6b. M4 → 获取文件内容/项目结构 → M2 (GitHubClient)
  6c. M4 → AST 分析 → M3 (AnalyzerRegistry) → ASTResult
  6d. M4 → ContextBuilder → AnalysisContext
  6e. M4 → 阶段一 → provider_fast.chat() → Phase1Result
  6f. M4 → 阶段二 (并行) → provider_strong.chat() × 4 → findings
  6g. M4 → PostProcessor → ReviewIssue[]
  6h. M4 → 返回 AnalysisResult
7. M5 → CommentCreator.build_*() → 格式化评论
8. M5 → create_review() → M2 (GitHubClient) → GitHub PR 评论
9. M5 → 保存 ReviewRecord + ReviewIssue[] → M1 (数据库)
10. M5 → 返回 200 OK
```

### 8.2 Dashboard 数据流

```
1. 用户浏览器 → GET /dashboard → M6
2. M6 → 验证 session → 查询 User
3. M6 → StatsService.get_overview_stats() → M1 → 统计数据
4. M6 → 渲染 Jinja2 模板 → HTML 返回
5. 浏览器 → HTMX GET /dashboard/stats → M6 → 返回 HTML fragment
6. Chart.js → 从 data-* 属性读取数据 → 渲染图表
```

### 8.3 手动 /review 命令

```
1. GitHub → POST /webhook/github → M5
2. M5 → parse_event → issue_comment event
3. M5 → 匹配 /review 正则
4. M5 → 权限校验 → M2 (GitHubClient)
5. 后续同 8.1 步骤 4-10
```

---

## 9. 路由与 API 规范

### 9.1 Webhook 端点

| 方法 | 路径 | 请求体 | 响应 | 说明 |
|------|------|--------|------|------|
| POST | `/webhook/github` | Webhook JSON | 200 / 401 | GitHub 事件唯一入口 |

### 9.2 页面路由（返回 HTML）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页（未登录→登录引导，已登录→Dashboard） |
| GET | `/auth/login` | GitHub OAuth 跳转 |
| GET | `/auth/callback` | OAuth 回调 |
| GET | `/dashboard` | Dashboard 主页面 |
| GET | `/reviews` | 评审记录列表 |
| GET | `/reviews/{id}` | 评审详情页 |
| GET | `/reviews/{id}/enhanced` | PR 增强详情视图 |
| GET | `/repositories` | 仓库列表页 |
| GET | `/repositories/{id}/config` | 仓库配置页 |

### 9.3 REST API 端点（HTMX 局部刷新 + JSON）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dashboard/stats` | Dashboard 统计数据 |
| GET | `/api/dashboard/trend` | 趋势数据（JSON → Chart.js） |
| GET | `/api/repositories` | 仓库列表（JSON） |
| GET | `/api/repositories/{id}/reviews` | 仓库评审记录（HTML fragment） |
| GET | `/api/reviews/{id}` | 评审详情数据（JSON） |
| PATCH | `/api/reviews/{id}/issues/{issue_id}` | 更新问题状态 |
| PUT | `/api/repositories/{id}/config` | 更新仓库配置 |

---

## 10. 项目目录结构

```
ReviewPilot/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 入口、路由注册、启动事件
│   │
│   ├── core/                      # M1: 基础设施
│   │   ├── __init__.py
│   │   ├── config.py              # 配置管理
│   │   ├── logging.py             # 日志配置
│   │   ├── exceptions.py          # 异常定义
│   │   └── database.py            # 数据库连接与会话管理
│   │
│   ├── models/                    # M1: 数据模型
│   │   ├── __init__.py
│   │   ├── repository.py
│   │   ├── pull_request.py
│   │   ├── review_record.py
│   │   ├── review_issue.py
│   │   ├── user.py
│   │   └── repo_config.py
│   │
│   ├── github/                    # M2: GitHub 集成
│   │   ├── __init__.py
│   │   ├── webhook.py             # Webhook 签名校验与事件解析
│   │   ├── client.py              # GitHub API 封装
│   │   └── schemas.py             # GitHub 数据结构
│   │
│   ├── analyzer/                  # M3: AST 分析
│   │   ├── __init__.py
│   │   ├── ast_base.py            # 分析器抽象基类
│   │   ├── python_analyzer.py     # Python AST 分析器
│   │   ├── java_analyzer.py       # Java AST 分析器
│   │   ├── registry.py            # 分析器注册表
│   │   └── schemas.py             # AST 结果数据结构
│   │
│   ├── engine/                    # M4: AI 分析引擎
│   │   ├── __init__.py
│   │   ├── provider.py            # AI Provider 抽象 + OpenAI 实现
│   │   ├── diff_parser.py         # Diff 解析器
│   │   ├── context_builder.py     # 分析上下文构建器
│   │   ├── orchestrator.py        # 两阶段分析编排器
│   │   ├── post_processor.py      # 结果后处理
│   │   ├── schemas.py             # 引擎数据结构
│   │   └── prompts/               # Prompt 模板
│   │       ├── system.py
│   │       ├── stage1.py
│   │       ├── stage2.py
│   │       └── templates/
│   │
│   ├── bot/                       # M5: GitHub Bot
│   │   ├── __init__.py
│   │   ├── event_router.py        # Webhook 事件路由
│   │   ├── auto_review.py         # 自动评审处理器
│   │   ├── command_handler.py     # /review 命令处理
│   │   └── comment_creator.py     # 评论格式化与创建
│   │
│   └── web/                       # M6: Web Dashboard
│       ├── __init__.py
│       ├── auth.py                # GitHub OAuth
│       ├── routes.py              # 页面路由 + API 路由
│       ├── stats_service.py       # 统计服务
│       └── enhanced_view.py       # 增强详情视图
│
├── templates/                     # Jinja2 模板 (M6)
│   ├── base.html
│   ├── auth/
│   ├── dashboard/
│   ├── reviews/
│   ├── repos/
│   └── shared/
│
├── static/                        # 静态资源 (Tailwind CSS 构建输出)
│   └── css/
│       └── app.css
│
├── tests/
│   ├── test_core/                 # M1 测试
│   ├── test_github/               # M2 测试
│   ├── test_analyzer/             # M3 测试
│   ├── test_engine/               # M4 测试
│   ├── test_bot/                  # M5 测试
│   └── test_web/                  # M6 测试
│
├── alembic/                       # 数据库迁移
├── doc/                           # 文档
│   ├── proposal.md
│   └── detailed-design.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── main.py                        # (已存在)
└── README.md
```

---

## 11. 关键技术细节

### 11.1 同步处理下的长时间请求处理

由于 v1 使用纯同步模式，AI 分析可能需要 30-90 秒。处理策略：

- FastAPI 设置足够的请求超时（120s）
- GitHub Webhook 有 10s 超时期望，但实际处理时间不受此限制（GitHub 只要求收到 200 响应）
- 流程：接收 Webhook → 验证签名 → 立即返回 200 → 同步执行分析 → 通过 GitHub API 创建评论
  - 注意：此模式下 GitHub 不会重试

**决策**：v1 先接受 Webhook 后立即返回 200，分析在后台同步执行（不是 async task queue，是同进程内的顺序执行）。如果分析失败，PR 上不创建评论，误差通过日志告警。

v2 改进方向：Webhook 接收后写入队列，立即返回 200，Worker 异步处理。

### 11.2 GitHub Review Comment 的行号定位

GitHub 的 Review Comment 需要指定 diff hunk 中的位置。定位策略：

1. 解析 unified diff 获取每个 hunk 的 old/new 行号映射
2. ReviewIssue 中记录的是文件的行号（新文件的行号）
3. CommentCreator 将新文件行号 → 映射到 diff hunk 中的位置 → 创建 comment
4. 如果行号在 diff 中找不到对应 hunk（例如问题在文件未变更部分），降级为 PR 对话评论

### 11.3 Prompt 中的语言配置

- `RepoConfig.language` 控制输出语言
- `zh`: 所有 AI 输出使用中文（问题标题、描述、建议）
- `en`: 使用英文
- 系统 prompt 中动态注入: `请使用{中文/英文}输出所有内容。`

---

## 12. 安全设计

| 关注点 | 措施 |
|--------|------|
| GitHub App 私钥 | 环境变量 `GITHUB_APP_PRIVATE_KEY`，不写入代码或配置文件中 |
| AI API Key | 环境变量，不与 GitHub 仓库同步 |
| Webhook 签名 | HMAC-SHA256 强制校验，拒绝未签名请求 |
| OAuth 安全 | 使用 GitHub OAuth 标准流程，state 参数防 CSRF |
| Session | httpOnly cookie + SameSite=Lax + 短期过期 |
| SQL 注入 | SQLAlchemy ORM 参数化查询 |
| 日志安全 | 不记录完整源码内容，仅记录文件路径和行号范围 |
| 访问控制 | 用户只能查看自己有权限的仓库评审数据 |

---

> 文档版本：v1.0 | 创建日期：2026-05-29 | 状态：待确认
