FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn && pip install --no-cache-dir openai

COPY . .

# Railway 会覆盖 PORT 环境变量
EXPOSE ${PORT:-5000}

# 模块路径：backend.app（WORKDIR 是 /app，代码结构是 /app/backend/*）
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 4 --threads 2 backend.app:app"]
