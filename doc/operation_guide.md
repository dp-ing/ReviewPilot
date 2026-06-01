# ReviewPilot 本机演示操作步骤

> 针对本机（Windows 10，D:\code\py\ReviewPilot），每条命令可直接复制粘贴执行。

---

## 速查表

| 项目 | 值 |
|------|-----|
| 项目目录 | `D:\code\py\ReviewPilot` |
| Python 环境 | `pytorch` (conda venv) |
| 服务端口 | `8765` |
| 测试代码 | `demo/test_repo/users.py`（已包含 SQL 注入等漏洞） |
| GitHub App ID | 3914887 |
| GitHub 仓库 | https://github.com/dp-ing/ReviewPilot |
| .env 文件 | 已配置好，7 个凭证已填写 |

---

## 一、启动服务

打开 **PowerShell**，依次执行：

```powershell
# 1. 进入项目目录
cd D:\code\py\ReviewPilot

# 2. 激活 conda 环境
conda activate pytorch

# 3. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8765
```

看到 `Application startup complete` 即启动成功。

**验证**：浏览器打开 `http://127.0.0.1:8765/health`，应显示 `{"status":"ok"}`。

---

## 二、创建测试仓库（首次演示前做一次）

### 2.1 在 GitHub 上创建新仓库

1. 浏览器打开 https://github.com/new
2. Repository name 填 `reviewpilot-demo`
3. 选择 **Private**（或 Public）
4. **不要勾选** "Initialize this repository with a README"
5. 点击 **Create repository**

记下仓库地址：`https://github.com/你的用户名/reviewpilot-demo`

### 2.2 把 demo 代码推上去

打开**新的 PowerShell 窗口**：

```powershell
# 1. 创建临时工作目录
mkdir D:\code\py\ReviewPilot\temp-demo
cd D:\code\py\ReviewPilot\temp-demo

# 2. 初始化 git 仓库
git init
git branch -M main

# 3. 复制测试代码（含漏洞的 users.py）
cp D:\code\py\ReviewPilot\demo\test_repo\users.py .

# 4. 创建 README
echo "# Demo Repo for ReviewPilot Testing" > README.md

# 5. 提交
git add users.py README.md
git commit -m "Initial commit: add vulnerable code for demo"

# 6. 关联远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/你的用户名/reviewpilot-demo.git

# 7. 推送
git -c http.proxy= -c https.proxy= push -u origin main
```

### 2.3 安装 ReviewPilot Bot 到这个仓库

1. 打开 https://github.com/settings/apps
2. 点击你的 GitHub App
3. 左侧点击 **Install App**
4. 选择 `reviewpilot-demo` 仓库
5. 点击 **Install**

---

## 三、启动 ngrok（让 GitHub 能访问本地服务）

打开**第三个 PowerShell 窗口**：

```powershell
ngrok http 8765
```

你会看到：

```
Forwarding  https://xxxx-xxx-xxx.ngrok-free.app -> http://localhost:8765
```

**记下这个 https 地址**，比如 `https://abc123.ngrok-free.app`。

### 更新 GitHub App 的 Webhook URL

1. 打开 https://github.com/settings/apps
2. 点击你的 App
3. 在 **Webhook URL** 填：`https://abc123.ngrok-free.app/webhook/github`
4. 点击 **Save changes**

> 每次重新启动 ngrok，地址会变，需要重新更新这个 URL。

---

## 四、创建测试 PR（演示 Bot 自动评审）

### 4.1 创建含漏洞的分支

在 `temp-demo` 目录的 PowerShell 中：

```powershell
cd D:\code\py\ReviewPilot\temp-demo

# 1. 创建并切换到新分支
git checkout -b feature/add-user-api

# 2. 确认 users.py 内容正确（应该包含 SQL 注入等漏洞）
cat users.py

# 3. 推送到 GitHub
git -c http.proxy= -c https.proxy= push origin feature/add-user-api
```

### 4.2 创建 Pull Request

浏览器打开你的仓库 `https://github.com/你的用户名/reviewpilot-demo`，GitHub 会提示你刚推送了 `feature/add-user-api` 分支，点击 **Compare & pull request** 按钮。

或者直接用这个链接（替换用户名）：

```
https://github.com/你的用户名/reviewpilot-demo/compare/main...feature/add-user-api
```

**PR 内容填写示例**：

- **标题**：`Add user search and delete API`
- **描述**：
  ```
  ## 变更内容
  - 新增用户搜索接口
  - 新增用户删除接口
  - 新增邮箱更新接口
  ```

点击 **Create pull request**。

### 4.3 等待 Bot 评审

创建 PR 后 **等待 10-30 秒**，刷新页面：

1. 代码行旁边会出现 **行级评论**（黄色/红色标记）
2. PR 底部会出现 **总结评论**（展示问题统计）

如果 30 秒后没出现，检查：
- ngrok 是否在运行
- Webhook URL 是否已更新为 ngrok 地址
- 终端日志有没有报错

---

## 五、演示手动 /review 命令

在刚才的 PR 页面底部评论框输入：

```
/review
```

点击 **Comment** 发送。等待 10 秒后刷新，会看到 Bot 的新分析评论。

还可以试试分类筛选：

```
/review focus:security
```

这条命令只触发安全类分析。

---

## 六、演示 Web Dashboard

### 6.1 登录

1. 浏览器打开 `http://127.0.0.1:8765/`
2. 看到深色渐变登录页
3. 点击 **使用 GitHub 账号登录**
4. 跳转 GitHub 授权后自动返回 Dashboard

### 6.2 展示各页面

按顺序点击左侧导航栏：

| 页面 | URL | 展示内容 |
|------|-----|---------|
| Dashboard | `/` | 4 张统计卡片 + 环形图 + 柱状图 |
| 仪表盘 | `/dashboard` | Chart.js 完整统计图表 |
| 评审记录 | `/reviews` | 分页列表，点击查看详情 |
| 增强视图 | 详情页点 "Enhanced View" | 按文件分组 + Alpine.js 交互 |
| 仓库管理 | `/repositories` | 仓库列表，点击 Config 进入配置 |

### 6.3 修改仓库配置（演示误报控制）

1. 进入 `/repositories` → 点击 **Config**
2. 关闭 **Style** 检查类别 → 点击保存
3. 调整灵敏度：高 / 中 / 低
4. 添加忽略规则：`**/test_*.py`

---

## 七、演示幻灯片

浏览器打开文件（不是 URL）：

```
D:\code\py\ReviewPilot\doc\demo_slides.html
```

- 按 `F11` 全屏
- 按 `→` 翻下一页，`←` 回上一页
- 也可以鼠标点击翻页

幻灯片内容：标题页 → 痛点 → 架构 → AST → Bot 流程 → Dashboard → 误报控制 → 质量指标 → 扩展方向

---

## 八、完整演示顺序（8-12 分钟）

| 步骤 | 时长 | 操作 |
|------|------|------|
| **Step 1** 幻灯片 | 2 分钟 | 打开 demo_slides.html，全屏翻页介绍架构 |
| **Step 2** Bot 评审 | 3 分钟 | 切到 GitHub，创建 PR，等 Bot 评论，展示行级评论 + 总结 |
| **Step 3** /review | 40 秒 | 在 PR 中发 `/review` 命令，展示手动触发 |
| **Step 4** Dashboard | 3 分钟 | 切到浏览器，登录 → 统计 → 列表 → 详情 → 增强视图 → 配置 |
| **Step 5** 幻灯片收尾 | 1 分钟 | 误报控制 + 质量指标 + 扩展方向 |

---

## 九、数据准备（确保图表不为空）

如果数据库是空的，图表会显示为 0。先检查：

```powershell
cd D:\code\py\ReviewPilot
python -c "
from app.core.database import SessionLocal
from app.models.review_record import ReviewRecord
db = SessionLocal()
print('评审记录数:', db.query(ReviewRecord).count())
db.close()
"
```

如果为 0，**先执行一次 Step 2（创建 PR + 触发评审）**，数据就有了。

---

## 十、常见问题

| 问题 | 解决办法 |
|------|---------|
| `http://127.0.0.1:8765` 打不开 | 确认 uvicorn 已启动，看到 `Application startup complete` |
| OAuth 回调报错 "redirect_uri not associated" | 去 GitHub OAuth App 设置把 callback URL 改为 `http://127.0.0.1:8765/auth/callback` |
| 端口被占用 | 换一个端口，`uvicorn app.main:app --reload --port 3000`，ngrok 也改为 `ngrok http 3000` |
| Bot 不评论 | 1. ngrok 是否在运行 2. Webhook URL 是否更新为 ngrok 地址 3. AI_API_KEY 是否有效 |
| Tailwind 样式不显示 | 需要网络连接，浏览器需能访问 cdn.tailwindcss.com |
| Dashboard 图表为空 | 数据库无评审记录，先触发一次评审 |
| 登录后跳转失败 | 检查 GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET 是否正确 |

---

> 更新日期：2026-06-01 | 针对本机 (Windows 10, pytorch conda env)
