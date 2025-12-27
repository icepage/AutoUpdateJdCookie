# 使用官方 Python 3.10.14 基础镜像
FROM python:3.10.14-slim

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 并安装依赖
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
RUN playwright install-deps
RUN playwright install chromium

# 时区
RUN apt-get install -y tzdata
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
# 复制应用文件
COPY . .

# 定义启动命令，运行 main.py
CMD ["python", "schedule_main.py"]
