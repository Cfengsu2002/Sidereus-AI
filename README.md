# AI 简历分析系统 · Resume Lab

后端：FastAPI · 前端：静态 HTML/CSS/JS（由 FastAPI 同源托管）

## 本地运行

### 环境

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 密钥

请勿把密钥提交到 Git。复制 `.env.example` 为 `.env`，填写：

- `OPENAI_API_KEY`（必选）
- 可选：`OPENAI_BASE_URL`、`OPENAI_MODEL`

### 启动后端（含前端静态页）

在项目根目录：

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

浏览器：**http://127.0.0.1:8000/**  

API：`GET /api/v1/health`，`POST /api/v1/resume/analyze`（`multipart/form-data`：`file` + `job_description`）

### Docker 打包与本地运行

根目录 **`Dockerfile`** 会把后端与 `frontend/` 打进镜像。

```bash
docker build -t resume-api:latest .
docker run --rm -p 9000:9000 --env-file .env -e PORT=9000 resume-api:latest
```

浏览器：**http://127.0.0.1:9000/**  

或使用 **`docker compose up --build`**（映射端口 9000）。

---

## 部署：Railway（推荐）

[Railway](https://railway.app) 会根据根目录 **`Dockerfile`** 构建并运行容器；平台会注入 **`PORT`**，镜像已自动监听该端口。

### 步骤概要

1. 把代码推到 **GitHub**（公开仓库便于笔试提交）。
2. 打开 Railway → **New Project** → **Deploy from GitHub repo**，选中本仓库。
3. **Variables** 里新增（不要写进代码仓库）：
   - `OPENAI_API_KEY`（必选）
   - 可选：`OPENAI_BASE_URL`、`OPENAI_MODEL`
4. 部署完成后，在 **Settings → Networking → Generate Domain** 得到 HTTPS 地址，例如 `https://xxx.up.railway.app`。
5. 浏览器打开该域名根路径即可使用上传页；接口仍为 `/api/v1/...`。

同一域名同时提供页面与 API，前端脚本在同源场景下无需配置 `api-base`。

### 若前端单独托管（GitHub Pages 等）

后端仍用 Railway 域名，在 **`frontend/index.html`** 取消注释并填写：

```html
<meta name="api-base" content="https://你的 railway 域名" />
```

---

## CORS

后端已 `allow_origins=["*"]`，GitHub Pages 等外站域名可调用 API。

---

## 笔试说明（环境与演示）

笔试原文曾提到阿里云 Serverless；若你选择 **Railway**，建议在 README 或提交说明里写一句：**后端以 Docker 部署于 Railway（容器的 Serverless 托管形态），REST API 与线上演示 URL**。最终以招聘方解读为准。

---

## 提交检查清单

- [ ] GitHub 公开仓库 + README 含你的线上地址说明
- [ ] 演示链接可打开并完成一次简历分析
- [ ] `OPENAI_API_KEY` 仅在 Railway Variables / 本地 `.env`，未写入代码
