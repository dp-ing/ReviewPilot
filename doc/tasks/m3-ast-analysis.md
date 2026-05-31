# M3 — AST 分析模块任务列表

> 模块职责：Python / Java 代码的 AST 解析与确定性规则检查
> 依赖：M1

---

## 子任务

### 3.1 基础结构

- [x] **PR-03-01** — 实现 `app/analyzer/schemas.py`
  - `ASTFinding` dataclass（rule_id, severity, category, file_path, line_start, line_end, title, description, code_snippet）
  - `FunctionInfo` + `ClassInfo` + `CallInfo` dataclass
  - `CodeStructure` dataclass
  - `ASTResult` dataclass（findings + structure）
- [x] **PR-03-02** — 实现 `app/analyzer/ast_base.py` — `ASTAnalyzer` 抽象基类
  - `get_supported_language()`, `analyze_file()`, `extract_structure()` 抽象方法
- [x] **PR-03-03** — 实现 `app/analyzer/registry.py` — `AnalyzerRegistry`
  - `register()`, `get(language)`, `detect_language(filename)`

### 3.2 Python AST 分析器 — 结构提取

- [x] **PR-03-04** — 实现 `app/analyzer/python_analyzer.py` — 骨架 + `get_supported_language()`
- [x] **PR-03-05** — 实现 `extract_structure()` — 提取函数/类/import/变量/异常处理块
- [x] **PR-03-06** — 编写结构提取测试（给定 Python 源码 → 断言函数数/类数/import 数正确）

### 3.3 Python AST 分析器 — 安全规则

- [x] **PR-03-07** — 实现 Critical 规则：`exec()`/`eval()` 调用检测（rule: python-exec-eval）
- [x] **PR-03-08** — 实现 Critical 规则：`pickle.loads()` 不受信数据检测（rule: python-unsafe-pickle）
- [x] **PR-03-09** — 实现 Critical 规则：`subprocess shell=True` 检测（rule: python-shell-injection）
- [x] **PR-03-10** — 编写安全规则测试（触发代码 → 断言产生问题 + 正常代码 → 断言无问题）

### 3.4 Python AST 分析器 — 逻辑/风格规则

- [x] **PR-03-11** — 实现 Warning 规则：SQL 字符串拼接（rule: python-sql-concat）
- [x] **PR-03-12** — 实现 Warning 规则：裸 except（rule: python-bare-except）
- [x] **PR-03-13** — 实现 Warning 规则：硬编码密码/密钥（rule: python-hardcoded-secret）
- [x] **PR-03-14** — 实现 Warning 规则：文件操作缺少 with（rule: python-file-leak）
- [x] **PR-03-15** — 实现 Warning 规则：圈复杂度 > 15（rule: python-complexity）
- [x] **PR-03-16** — 实现 Suggestion 规则：函数长度 > 50 行（rule: python-function-length）
- [x] **PR-03-17** — 编写逻辑/风格规则测试
- [x] **PR-03-18** — 实现 `analyze_file()` 方法（串联所有规则 + 结构提取，返回 `ASTResult`）
- [x] **PR-03-19** — 编写 Python 分析器集成测试（完整 Python 文件扫描）

### 3.5 Java AST 分析器

- [x] **PR-03-20** — 实现 `app/analyzer/java_analyzer.py` — 骨架 + 结构提取（类/方法/import/注解）
- [x] **PR-03-21** — 实现 Critical 规则：`Runtime.exec()` 命令注入（rule: java-command-injection）
- [x] **PR-03-22** — 实现 Critical 规则：不安全反序列化（rule: java-unsafe-deserial）
- [x] **PR-03-23** — 实现 Warning 规则：Statement SQL 拼接（rule: java-sql-concat）
- [x] **PR-03-24** — 实现 Warning 规则：资源未使用 try-with-resources（rule: java-resource-leak）
- [x] **PR-03-25** — 实现 Warning 规则：硬编码密码/密钥（rule: java-hardcoded-secret）
- [x] **PR-03-26** — 实现 Warning 规则：圈复杂度 > 15（rule: java-complexity）
- [x] **PR-03-27** — 实现 Suggestion 规则：方法长度 > 50 行 / 未处理异常（rule: java-method-length / java-unhandled-exception）
- [x] **PR-03-28** — 实现 `analyze_file()` + 集成测试

### 3.6 误报控制

- [x] **PR-03-29** — 伪阳性规避规则（如 SQLAlchemy 等 ORM 库的调用不触发 SQL 注入告警）
- [x] **PR-03-30** — 编写误报控制测试（常见安全库用法不触发告警）

---

## 完成标准

- [x] AnalyzerRegistry 正确按文件名后缀识别语言并分发分析器
- [x] Python 分析器 10 条规则全部通过单测（触发 + 正常）
- [x] Java 分析器 8 条规则全部通过单测（触发 + 正常）
- [x] 结构提取正确（函数边界、类定义、import 列表）
- [x] 误报规避机制有效（ORM 等库调用不误报）
