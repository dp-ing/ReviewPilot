# ReviewPilot 本机演示操作步骤

> 针对本机（Windows 10，D:\code\py\ReviewPilot），从头到尾演示一遍给评审看。

---

## 你需要的所有信息速查

| 项目 | 值 |
|------|-----|
| 项目目录 | `D:\code\py\ReviewPilot` |
| GitHub 仓库 | https://github.com/dp-ing/ReviewPilot |
| Python 环境 | `pytorch` (conda venv) |
| 服务端口 | `8765`（8000 端口有僵尸进程，改用 8765） |
| .env 文件 | 已配置好，所有 7 个凭证已填写 |
| GitHub App ID | 3914887 |
| AI 模型 | deepseek-v4-flash (阶段一) + deepseek-v4-pro (阶段二) |

---

## 一、启动服务

### 1. 打开终端

打开 PowerShell，进入项目目录并激活 conda 环境：

```powershell
cd D:\code\py\ReviewPilot
conda activate pytorch
```

### 2. 启动服务

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8765
```

看到 `Application startup complete` 就表示启动成功。

### 3. 验证

浏览器打开 `http://127.0.0.1:8765`，应看到登录页面。

健康检查：`http://127.0.0.1:8765/health` 返回 `{"status":"ok"}`。

---

## 二、演示前准备（按顺序做）

### 准备 A：确保 Dashboard 有数据

你的数据库 `reviewpilot.db` 在项目根目录。如果里面没有评审数据，Dashboard 图表会显示为 0。

检查数据：

```powershell
cd D:\code\py\ReviewPilot
python -c "
from app.core.database import SessionLocal
from app.models.review_record import ReviewRecord
db = SessionLocal()
count = db.query(ReviewRecord).count()
print(f'评审记录数: {count}')
db.close()
"
```

如果为 0，你需要先触发一两次评审来产生数据。用 GitHub Bot 自动评审或手动 `/review` 都可以。

### 准备 B：演示幻灯片

浏览器打开 `D:\code\py\ReviewPilot\doc\demo_slides.html`：
- 按 `F11` 全屏
- 按 `→` 翻下一页，`←` 回上一页
- 点击也可以翻页

### 准备 C：浏览器标签页

提前打开以下页面（各一个标签）：

| 标签 | URL | 用途 |
|------|-----|------|
| 登录页 | `http://127.0.0.1:8765/` | 展示 OAuth 登录 |
| 仪表盘 | `http://127.0.0.1:8765/dashboard` | 展示统计图表 |
| 评审列表 | `http://127.0.0.1:8765/reviews` | 展示评审记录 |

---

## 三、演示顺序

按照 `doc/demo_script.md` 的流程，演示顺序如下：

### Step 1：幻灯片介绍（约 2 分钟）

切换到 `demo_slides.html` 标签页，翻页介绍：
1. 标题页 → 项目名称和定位
2. 痛点 → 四个代码评审痛点
3. 架构 → 两阶段 AI 分析流程
4. AST 规则 → Python 10 条 + Java 8 条
5. Bot 流程 → 6 步自动评审链路

### Step 2：GitHub Bot 自动评审（约 3 分钟）

1. 切换到 GitHub，进入测试仓库
2. 创建一个新 PR，代码里包含 SQL 注入问题：

```python
def search_users():
    name = request.args.get("name", "")
    query = "SELECT * FROM users WHERE name = '" + name + "'"
    cursor.execute(query)
```

3. 提交 PR 后等待 10-20 秒
4. 刷新页面，展示 Bot 自动创建的行级评论和总结报告

### Step 3：手动 /review 命令（约 40 秒）

1. 在 PR 评论框输入 `/review` 并发送
2. 等待并刷新，展示 Bot 追加的评论

### Step 4：Web Dashboard（约 3 分钟）

1. 切换到 `http://127.0.0.1:8765/`
2. 点击 "Login with GitHub" → 授权 → 回到首页
3. 展示四个统计卡片
4. 切换到 `/dashboard` 展示 Chart.js 图表
5. 切换到 `/reviews` 展示评审列表
6. 点击一条记录展示详情
7. 点击 "Enhanced View" 展示增强视图
8. 切换到 `/repositories` → 点击 Config 展示配置页

### Step 5：幻灯片收尾（约 1 分钟）

切换到 `demo_slides.html`：
1. 误报控制策略（Slide 7）
2. 质量指标（Slide 8）
3. 扩展方向（Slide 9）

---

## 四、暴露 Webhook（如需演示 Bot 功能）

Bot 自动评审需要 GitHub 能访问到你的服务。如果你要**实时演示** Bot 创建评论的过程，需要用 ngrok：

### 1. 启动 ngrok

打开新终端：

```powershell
ngrok http 8765
```

记下输出的 https 地址，如 `https://abc123.ngrok-free.app`。

### 2. 更新 GitHub App Webhook URL

1. 打开 https://github.com/settings/apps
2. 点击你的 App
3. Webhook URL 改为 `https://你的地址/webhook/github`
4. 点击 Save

### 3. 演示完还原

演示结束后改回原来的 Webhook URL。

> 如果 ngrok 不稳定，可以提前录好 Bot 创建评论的视频片段作为备选方案。

---

## 五、数据库初始化（如果 .db 文件丢失或损坏）

```powershell
cd D:\code\py\ReviewPilot

# 先确保数据库文件存在，运行迁移
alembic upgrade head
```

如果 alembic 报错，也可以直接用 Python 创建表：

```powershell
python -c "
from app.core.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('数据库表已创建')
"
```

---

## 六、运行测试（可选，证明代码质量）

```powershell
# 运行全部测试（跳过需要 API Key 的 E2E 测试）
pytest tests/ -v --ignore=tests/test_engine/test_prompts.py -k "not e2e"

# 或用全参数
pytest tests/ -v --cov=app --cov-report=term-missing -k "not e2e"

# 类型检查
mypy app/ --strict

# 代码风格检查
ruff check app/
```

---

## 七、常见问题

| 问题 | 解决办法 |
|------|---------|
| `http://127.0.0.1:8765` 打不开 | 确认 uvicorn 已启动，看到 `Application startup complete` |
| 端口被占用 | 换一个端口，如 `--port 3000` |
| Dashboard 图表为空 | 数据库无评审记录，需先触发评审 |
| 登录后跳转失败 | 检查 GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET 是否正确，OAuth callback URL 是否匹配 |
| Tailwind CSS 样式不显示 | 需要网络连接加载 CDN |
| Bot 不评论 | 检查 AI_API_KEY 是否有效，ngrok 是否运行，Webhook URL 是否更新 |

---

## 八、演示用测试代码

### Python SQL 注入示例（创建 PR 用）

```python
# users.py - 用于演示安全检测
from flask import request, jsonify
import sqlite3

def search_users():
    """Search users by name — VULNERABLE to SQL injection"""
    name = request.args.get("name", "")
    conn = sqlite3.connect("app.db")
    query = "SELECT * FROM users WHERE name = '" + name + "'"
    cursor = conn.execute(query)
    results = cursor.fetchall()
    conn.close()
    return jsonify(results)

def delete_user(user_id):
    """Delete user — VULNERABLE to SQL injection"""
    conn = sqlite3.connect("app.db")
    query = f"DELETE FROM users WHERE id = {user_id}"
    conn.execute(query)
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})
```

---

> 更新日期：2026-05-31 | 针对本机 (Windows 10, pytorch conda env)
