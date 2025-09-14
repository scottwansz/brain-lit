# 使用官方Python运行时作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装uv包管理器
RUN pip install uv

# 复制依赖文件
COPY pyproject.toml ./
COPY src/ ./src/

# 使用uv安装依赖到系统环境中
RUN uv pip install --system --no-cache-dir .

# 暴露端口（Streamlit默认端口）
EXPOSE 8501

# 运行应用
CMD ["streamlit", "run", "src/brain_lit/app.py", "--server.port=8501", "--server.address=0.0.0.0"]