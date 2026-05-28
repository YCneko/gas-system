FROM python:3.13-slim

WORKDIR /app

# 安装 Python 依赖（PyMySQL 是纯 Python 驱动，无需系统编译工具）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制源码
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
