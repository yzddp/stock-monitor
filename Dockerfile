# 使用官方Python轻量级镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将依赖文件复制到容器中
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 将应用代码复制到容器中
COPY . .

# 声明容器运行时暴露的端口（需要与您app.py中运行的端口一致，例如9000）
EXPOSE 9000

# 启动命令
CMD ["python", "app.py"]
