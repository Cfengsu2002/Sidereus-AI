# 通用容器入口：Railway / 本地 Docker / 可选阿里云 FC 等
# Railway 会注入 PORT；本地可设 PORT=9000。Apple Silicon 打 linux 镜像：--platform linux/amd64

FROM python:3.11-slim-bookworm

WORKDIR /code

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend

# 监听端口优先级：Railway 的 PORT > FC_SERVER_PORT（阿里云）> 默认 8000
ENV PORT=8000

EXPOSE 8000

# 必须监听 0.0.0.0，不能用 127.0.0.1
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-${FC_SERVER_PORT:-8000}}"]
