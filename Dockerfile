FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY . /app

# 安装 pip 依赖 (由于我们去掉了 SQLAlchemy 等复杂库，现在安装会极快)
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
    && pip config set global.trusted-host mirrors.cloud.tencent.com \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 80

CMD ["python3", "run.py"]
