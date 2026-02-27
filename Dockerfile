FROM python:3.11-slim

WORKDIR /app

# 避免生成 .pyc，日志及时输出
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝代码
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY .env ./.env

EXPOSE 8000

CMD ["sh", "-c", "until alembic upgrade head; do echo 'waiting for mysql...'; sleep 2; done; uvicorn app.main:app --host 0.0.0.0 --port 8000"]
