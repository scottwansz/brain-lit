# 使用官方Python运行时作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装uv并使用它来安装Python依赖到系统环境中，使用华为镜像源
RUN pip install --no-cache-dir -i https://mirrors.huaweicloud.com/repository/pypi/simple uv \
    && uv pip install --system --no-cache-dir --index https://mirrors.huaweicloud.com/repository/pypi/simple .

# 复制项目文件
COPY . .

# 暴露端口（Streamlit默认端口）
EXPOSE 8501

# 运行应用
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]