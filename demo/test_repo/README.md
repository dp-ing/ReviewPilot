# Demo 测试仓库

> 本目录模拟一个 GitHub 测试仓库，用于演示 ReviewPilot 的 PR 评审功能。
> 代码中**故意包含**安全漏洞和代码问题，供 Bot 检测。

## 使用方法

1. 在 GitHub 上创建一个测试仓库（或使用已有仓库）
2. 将本目录下的文件上传或提交到测试仓库
3. 创建一个 Pull Request
4. ReviewPilot Bot 将自动分析并创建评审评论

## 包含的测试场景

| 文件 | 问题类型 | 严重级别 |
|------|---------|---------|
| `users.py` | SQL 注入、缺少异常处理 | Critical + Warning |
| `admin.py` | 命令注入、硬编码密钥 | Critical + Warning |
| `utils.py` | 裸 except、文件泄漏 | Warning |

## 期望检测结果

- **3 个 Critical**: SQL 注入 ×2 + 命令注入 ×1
- **3 个 Warning**: 硬编码密钥 + 裸 except + 文件泄漏
- **2 个 Suggestion**: 函数过长 + 代码风格
