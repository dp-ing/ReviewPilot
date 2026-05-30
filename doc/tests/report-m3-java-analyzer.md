# M3 Java Analyzer 测试报告

> 生成日期：2026-05-30 | 测试总数：254 | 通过：254 | 失败：0

---

## 总览

| 模块 | 测试文件 | 测试数 | 通过 | 失败 |
|------|---------|--------|------|------|
| Python 分析器 | test_python_analyzer.py | 80 | 80 | 0 |
| Java 分析器 | test_java_analyzer.py | 51 | 51 | 0 |
| 其他模块 | test_ast_base.py + test_registry.py + test_schemas.py + test_config.py + test_database.py + test_exceptions.py + test_logging.py + test_models.py + test_client.py + test_schemas_gh.py + test_webhook.py | 123 | 123 | 0 |
| **合计** | | **254** | **254** | **0** |

---

## Java 分析器测试详情（51 tests）

### 结构提取测试 (12 tests)

| # | 测试名称 | 状态 |
|---|---------|------|
| 1 | test_is_ast_analyzer | PASSED |
| 2 | test_get_supported_language | PASSED |
| 3 | test_extract_structure_returns_code_structure | PASSED |
| 4 | test_extract_structure_imports | PASSED |
| 5 | test_extract_structure_class | PASSED |
| 6 | test_extract_structure_class_with_inheritance | PASSED |
| 7 | test_extract_structure_methods | PASSED |
| 8 | test_extract_structure_calls | PASSED |
| 9 | test_extract_structure_lines_of_code | PASSED |
| 10 | test_extract_structure_empty_file | PASSED |
| 11 | test_analyze_file_returns_ast_result | PASSED |
| 12 | test_analyze_file_with_syntax_error | PASSED |

### 安全规则测试 (27 tests)

#### 命令注入检测 (2 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 13 | test_detect_runtime_exec | PASSED |
| 14 | test_no_alert_on_safe_call | PASSED |

#### 不安全反序列化检测 (3 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 15 | test_detect_read_object | PASSED |
| 16 | test_detect_read_unshared | PASSED |
| 17 | test_no_alert_on_safe_call | PASSED |

#### SQL 拼接检测 (6 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 18 | test_detect_execute_query_with_concat | PASSED |
| 19 | test_detect_execute_update_with_concat | PASSED |
| 20 | test_detect_execute_with_concat | PASSED |
| 21 | test_detect_add_batch_with_concat | PASSED |
| 22 | test_no_alert_on_static_query | PASSED |
| 23 | test_no_alert_on_safe_call | PASSED |

#### 资源泄漏检测 (4 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 24 | test_detect_file_input_stream_without_try_resource | PASSED |
| 25 | test_detect_file_reader_without_try_resource | PASSED |
| 26 | test_no_alert_on_try_with_resources | PASSED |
| 27 | test_no_alert_on_safe_call | PASSED |

#### 硬编码密钥检测 (7 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 28 | test_detect_password | PASSED |
| 29 | test_detect_api_key | PASSED |
| 30 | test_detect_token | PASSED |
| 31 | test_no_alert_on_env_read | PASSED |
| 32 | test_no_alert_on_empty_string | PASSED |
| 33 | test_no_alert_on_normal_variable | PASSED |
| 34 | test_no_alert_on_test_value | PASSED |

### 逻辑/风格规则测试 (6 tests)

#### 圈复杂度检测 (3 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 35 | test_detect_high_complexity | PASSED |
| 36 | test_no_alert_on_simple_function | PASSED |
| 37 | test_no_alert_on_empty_function | PASSED |

#### 方法长度检测 (3 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 38 | test_detect_long_method | PASSED |
| 39 | test_no_alert_on_short_function | PASSED |
| 40 | test_no_alert_on_empty_function | PASSED |

### 集成测试 (7 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 41 | test_integration_finds_command_injection | PASSED |
| 42 | test_integration_finds_unsafe_deserial | PASSED |
| 43 | test_integration_finds_sql_concat | PASSED |
| 44 | test_integration_finds_resource_leak | PASSED |
| 45 | test_integration_finds_hardcoded_secret | PASSED |
| 46 | test_integration_structure_extracted | PASSED |
| 47 | test_integration_all_findings_have_required_fields | PASSED |

### 误报控制测试 (4 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 48 | test_no_alert_on_literal_exec_arg | PASSED |
| 49 | test_no_alert_on_literal_sql_concat | PASSED |
| 50 | test_still_detects_sql_concat_with_variable | PASSED |
| 51 | test_still_detects_runtime_exec_with_variable | PASSED |

---

## Java 规则覆盖清单

| 规则 ID | 严重级别 | 类别 | 测试数 | 状态 |
|----------|---------|------|--------|------|
| java-command-injection | critical | security | 2 | 已实现 |
| java-unsafe-deserial | critical | security | 3 | 已实现 |
| java-sql-concat | warning | security | 6 | 已实现 |
| java-resource-leak | warning | best_practice | 4 | 已实现 |
| java-hardcoded-secret | warning | security | 7 | 已实现 |
| java-complexity | warning | style | 3 | 已实现 |
| java-method-length | suggestion | style | 3 | 已实现 |

---

## 代码质量

| 检查 | 结果 |
|------|------|
| mypy --strict | Success: no issues found |
| ruff check | All checks passed! |
| pytest 覆盖率 | 254/254 passed |
