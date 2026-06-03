"""
Demo data processor — 故意包含多种安全漏洞，用于测试 ReviewPilot AST 检测能力。
请勿在生产环境中使用此代码！
"""
import pickle
import subprocess
import os

# ============================================================
# Critical: 硬编码密钥/密码 (hardcoded-secret)
# ============================================================
DB_HOST = "192.168.1.100"
DB_USER = "admin"
DB_PASSWORD = "P@ssw0rd!2024"
API_SECRET_KEY = "sk-proj-abc123xyz-demo-secret-key"
REDIS_AUTH_TOKEN = "redis-token-8a7b9c3d"

# ============================================================
# Critical: subprocess shell=True 命令注入 (shell-injection)
# ============================================================
def run_backup_script(db_name: str, user_input: str) -> str:
    """执行数据库备份 — VULNERABLE: shell=True 命令注入"""
    cmd = f"pg_dump {db_name} | gzip > /backup/{user_input}.gz"
    subprocess.call(cmd, shell=True)
    return f"Backup saved to /backup/{user_input}.gz"


def restart_service(service_name: str) -> None:
    """重启服务 — VULNERABLE: shell=True"""
    subprocess.run(f"systemctl restart {service_name}", shell=True)


# ============================================================
# Critical: eval 动态执行 (exec-eval)
# ============================================================
def calculate_expression(expr: str) -> float:
    """计算用户输入的数学表达式 — VULNERABLE: eval 动态执行"""
    return eval(expr)


def execute_user_code(code: str) -> dict:
    """执行用户提交的 Python 代码 — VULNERABLE: exec"""
    local_vars = {}
    exec(code, {"__builtins__": {}}, local_vars)
    return {"result": local_vars.get("result", None)}


# ============================================================
# Critical: pickle 不安全反序列化 (unsafe-pickle)
# ============================================================
def load_user_session(data: bytes) -> dict:
    """加载用户会话 — VULNERABLE: pickle.loads 不安全反序列化"""
    return pickle.loads(data)


def cache_restore(blob: bytes) -> object:
    """从缓存恢复对象 — VULNERABLE: pickle.loads"""
    return pickle.loads(blob)


# ============================================================
# Warning: 文件操作未使用 with 语句 (file-leak)
# ============================================================
def read_config_file(filepath: str) -> str:
    """读取配置文件 — VULNERABLE: 未使用 with 语句"""
    f = open(filepath, "r")
    content = f.read()
    f.close()
    return content


def write_log_file(log_path: str, message: str) -> None:
    """写入日志 — VULNERABLE: 未使用 with 语句，异常时泄漏文件句柄"""
    f = open(log_path, "a")
    f.write(message + "\n")
    f.close()


# ============================================================
# Warning: 裸 except (bare-except)
# ============================================================
def parse_json_safe(json_str: str) -> dict:
    """解析 JSON — VULNERABLE: 裸 except 掩盖了具体异常"""
    import json
    try:
        return json.loads(json_str)
    except:
        return {}


def safe_divide(a: float, b: float) -> float:
    """除法 — VULNERABLE: 裸 except"""
    try:
        return a / b
    except:
        return 0.0


# ============================================================
# Warning: 圈复杂度 > 15 (python-complexity)
# ============================================================
def process_transaction(data: list, mode: str, threshold: int, options: dict) -> list:
    """处理交易数据 — 圈复杂度极高，多种路径分支"""
    results = []
    for item in data:
        if mode == "filter":
            if item > threshold:
                if options.get("strict", False):
                    if item > threshold * 2:
                        if options.get("double_tag", False):
                            results.append({"value": item * 2, "tag": "double"})
                        else:
                            results.append(item * 2)
                    elif item > threshold * 1.5:
                        if options.get("round", False):
                            results.append(round(item))
                        else:
                            results.append(item * 1.5)
                else:
                    results.append(item)
            elif item > 0:
                if options.get("include_zero", False):
                    results.append(0)
                elif options.get("negative_only", False):
                    results.append(-item)
        elif mode == "transform":
            if isinstance(item, int):
                if item < 0:
                    results.append(abs(item))
                elif item == 0:
                    results.append(1)
                else:
                    if item % 2 == 0:
                        results.append(item * item)
                    else:
                        results.append(item * 2 + 1)
            elif isinstance(item, float):
                if item.is_integer():
                    results.append(int(item))
                else:
                    results.append(round(item, 2))
            elif isinstance(item, str):
                if item.isdigit():
                    results.append(int(item) * 10)
                elif item:
                    results.append(item.upper())
        elif mode == "aggregate":
            total = sum(x for x in data if isinstance(x, (int, float)))
            if total > 100:
                if options.get("normalize", False):
                    for x in data:
                        if isinstance(x, (int, float)) and total > 0:
                            results.append(x / total)
            elif total < 0:
                raise ValueError(f"Negative total: {total}")
            elif total == 0:
                if options.get("empty_as_none", True):
                    results.append(None)
        elif mode == "passthrough":
            results = list(data)
        else:
            pass
    return results


# ============================================================
# Suggestion: 函数长度 > 50 行 (python-function-length)
# ============================================================
def build_html_report(records: list, title: str, author: str, date: str) -> str:
    """构建 HTML 报告 — 函数过长，应拆分"""
    lines = []
    lines.append("<!DOCTYPE html>")
    lines.append("<html>")
    lines.append("<head>")
    lines.append(f"  <title>{title}</title>")
    lines.append('  <meta charset="UTF-8">')
    lines.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    lines.append('  <style>')
    lines.append("    body { font-family: Arial, sans-serif; margin: 20px; }")
    lines.append("    table { border-collapse: collapse; width: 100%; }")
    lines.append("    th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }")
    lines.append("    th { background-color: #f0f0f0; }")
    lines.append("    .critical { color: red; font-weight: bold; }")
    lines.append("    .warning { color: orange; }")
    lines.append("    .footer { margin-top: 20px; font-size: 12px; color: #666; }")
    lines.append("  </style>")
    lines.append("</head>")
    lines.append("<body>")
    lines.append(f"  <h1>{title}</h1>")
    lines.append(f"  <p>Author: {author}</p>")
    lines.append(f"  <p>Date: {date}</p>")
    lines.append(f"  <p>Total Records: {len(records)}</p>")
    lines.append('  <hr>')
    lines.append('  <table>')
    lines.append('    <thead>')
    lines.append('      <tr>')
    if records and len(records) > 0:
        for key in records[0].keys():
            lines.append(f"        <th>{key}</th>")
    lines.append('      </tr>')
    lines.append('    </thead>')
    lines.append('    <tbody>')
    for record in records:
        lines.append('      <tr>')
        for key, value in record.items():
            if isinstance(value, (int, float)):
                lines.append(f"        <td>{value}</td>")
            elif isinstance(value, str) and "error" in value.lower():
                lines.append(f'        <td class="critical">{value}</td>')
            elif isinstance(value, str) and "warning" in value.lower():
                lines.append(f'        <td class="warning">{value}</td>')
            else:
                lines.append(f"        <td>{value}</td>")
        lines.append('      </tr>')
    lines.append('    </tbody>')
    lines.append('  </table>')
    lines.append(f'  <div class="footer">Report generated by {author} on {date}</div>')
    lines.append("</body>")
    lines.append("</html>")
    return "\n".join(lines)


# ============================================================
# 更多硬编码密钥（不同变量名模式）
# ============================================================
SMTP_PASSWD = "mailpass123"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
THIRD_PARTY_TOKEN = "tpl-sk-8f3a2b1c9d4e"
