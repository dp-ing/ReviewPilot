# M3 Python Analyzer 测试报告

> 生成日期：2026-05-30 | 测试总数：203 | 通过：203 | 失败：0

---

## 总览

| 模块 | 测试文件 | 测试数 | 通过 | 失败 |
|------|---------|--------|------|------|
| AST 分析器 | test_ast_base.py | 4 | 4 | 0 |
| Python 分析器 | test_python_analyzer.py | 80 | 80 | 0 |
| 注册表 | test_registry.py | 5 | 5 | 0 |
| 数据结构 | test_schemas.py | 11 | 11 | 0 |
| 配置 | test_config.py | 6 | 6 | 0 |
| 数据库 | test_database.py | 4 | 4 | 0 |
| 异常 | test_exceptions.py | 14 | 14 | 0 |
| 日志 | test_logging.py | 5 | 5 | 0 |
| 数据模型 | test_models.py | 33 | 33 | 0 |
| GitHub 客户端 | test_client.py | 10 | 10 | 0 |
| GitHub 数据结构 | test_schemas.py | 13 | 13 | 0 |
| GitHub Webhook | test_webhook.py | 18 | 18 | 0 |
| **合计** | | **203** | **203** | **0** |

---

## Python 分析器测试详情（80 tests）

### 结构提取测试 (23 tests)

| # | 测试名称 | 状态 |
|---|---------|------|
| 1 | test_is_ast_analyzer | PASSED |
| 2 | test_get_supported_language | PASSED |
| 3 | test_extract_structure_returns_code_structure | PASSED |
| 4 | test_extract_structure_imports | PASSED |
| 5 | test_extract_structure_functions | PASSED |
| 6 | test_extract_structure_classes | PASSED |
| 7 | test_extract_empty_file | PASSED |
| 8 | test_extract_structure_calls | PASSED |
| 9 | test_extract_structure_calls_with_args_and_kwargs | PASSED |
| 10 | test_extract_structure_variable_assignments | PASSED |
| 11 | test_extract_structure_exception_blocks | PASSED |
| 12 | test_extract_structure_function_decorators | PASSED |
| 13 | test_extract_structure_function_return_type | PASSED |
| 14 | test_extract_structure_async_function | PASSED |
| 15 | test_extract_structure_class_with_bases | PASSED |
| 16 | test_extract_structure_class_decorators | PASSED |
| 17 | test_extract_structure_lines_of_code | PASSED |
| 18 | test_extract_structure_complexity | PASSED |
| 19 | test_extract_structure_mixed_async_and_sync | PASSED |
| 20 | test_extract_structure_nested_classes_and_functions | PASSED |
| 21 | test_extract_structure_lambda_is_not_function | PASSED |
| 22 | test_extract_structure_module_docstring | PASSED |
| 23 | test_extract_structure_no_exception_blocks | PASSED |

### 安全规则测试 (34 tests)

#### exec/eval 检测 (8 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 24 | test_detect_exec_call | PASSED |
| 25 | test_detect_eval_call | PASSED |
| 26 | test_detect_both_exec_and_eval | PASSED |
| 27 | test_detect_exec_inside_function | PASSED |
| 28 | test_no_false_positive_on_safe_calls | PASSED |
| 29 | test_no_false_positive_on_attributed_exec | PASSED |
| 30 | test_analyze_file_returns_ast_result | PASSED |
| 31 | test_analyze_file_with_syntax_error | PASSED |

#### pickle 反序列化检测 (5 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 32 | test_detect_pickle_loads | PASSED |
| 33 | test_detect_pickle_load | PASSED |
| 34 | test_detect_dill_loads | PASSED |
| 35 | test_no_false_positive_on_json_loads | PASSED |
| 36 | test_no_false_positive_on_pickle_module | PASSED |

#### shell 注入检测 (8 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 37 | test_detect_os_system | PASSED |
| 38 | test_detect_os_popen | PASSED |
| 39 | test_detect_subprocess_call_shell_true | PASSED |
| 40 | test_detect_subprocess_run_shell_true | PASSED |
| 41 | test_detect_subprocess_popen_shell_true | PASSED |
| 42 | test_no_alert_on_subprocess_without_shell | PASSED |
| 43 | test_no_alert_on_subprocess_shell_false | PASSED |
| 44 | test_no_alert_on_safe_calls | PASSED |

#### SQL 拼接检测 (7 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 45 | test_detect_execute_with_string_concat | PASSED |
| 46 | test_detect_execute_with_fstring | PASSED |
| 47 | test_detect_execute_with_percent_format | PASSED |
| 48 | test_detect_executemany_with_concat | PASSED |
| 49 | test_no_alert_on_parameterized_query | PASSED |
| 50 | test_no_alert_on_static_query | PASSED |
| 51 | test_no_alert_on_safe_function | PASSED |

#### 硬编码密钥检测 (7 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 52 | test_detect_password | PASSED |
| 53 | test_detect_api_key | PASSED |
| 54 | test_detect_token | PASSED |
| 55 | test_no_alert_on_env_read | PASSED |
| 56 | test_no_alert_on_test_value | PASSED |
| 57 | test_no_alert_on_empty_string | PASSED |
| 58 | test_no_alert_on_normal_variable | PASSED |

### 逻辑/风格规则测试 (14 tests)

#### 裸 except 检测 (4 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 59 | test_detect_bare_except | PASSED |
| 60 | test_no_alert_on_typed_except | PASSED |
| 61 | test_no_alert_on_multiple_except | PASSED |
| 62 | test_no_alert_on_no_try | PASSED |

#### 文件泄漏检测 (4 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 63 | test_detect_open_without_with | PASSED |
| 64 | test_no_alert_on_with_open | PASSED |
| 65 | test_no_alert_on_with_open_multiline | PASSED |
| 66 | test_no_alert_on_other_call | PASSED |

#### 圈复杂度检测 (3 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 67 | test_detect_high_complexity | PASSED |
| 68 | test_no_alert_on_simple_function | PASSED |
| 69 | test_no_alert_on_empty_function | PASSED |

#### 函数长度检测 (2 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 70 | test_detect_long_function | PASSED |
| 71 | test_no_alert_on_short_function | PASSED |

### 集成测试 (9 tests)
| # | 测试名称 | 状态 |
|---|---------|------|
| 72 | test_integration_finds_exec_eval | PASSED |
| 73 | test_integration_finds_unsafe_pickle | PASSED |
| 74 | test_integration_finds_shell_injection | PASSED |
| 75 | test_integration_finds_sql_concat | PASSED |
| 76 | test_integration_finds_hardcoded_secret | PASSED |
| 77 | test_integration_finds_file_leak | PASSED |
| 78 | test_integration_no_bare_except_on_safe_function | PASSED |
| 79 | test_integration_structure_extracted | PASSED |
| 80 | test_integration_all_findings_have_required_fields | PASSED |

---

## Python 规则覆盖清单

| 规则 ID | 严重级别 | 类别 | 测试数 | 状态 |
|----------|---------|------|--------|------|
| python-exec-eval | critical | security | 8 | 已实现 |
| python-unsafe-pickle | critical | security | 5 | 已实现 |
| python-shell-injection | critical | security | 8 | 已实现 |
| python-sql-concat | warning | security | 7 | 已实现 |
| python-bare-except | warning | best_practice | 4 | 已实现 |
| python-hardcoded-secret | warning | security | 7 | 已实现 |
| python-file-leak | warning | best_practice | 4 | 已实现 |
| python-complexity | warning | style | 3 | 已实现 |
| python-function-length | suggestion | style | 2 | 已实现 |
| python-duplicate | suggestion | style | — | 待实现 |

---

## 代码质量

| 检查 | 结果 |
|------|------|
| mypy --strict | Success: no issues found |
| ruff check | All checks passed! |
| pytest 覆盖率 | 203/203 passed |
