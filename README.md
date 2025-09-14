# brain-lit

这是一个Python项目，具有Docker支持。

## 项目结构

```
.
├── src/
│   └── brain_lit/
│       ├── __init__.py
│       ├── app.py
│       ├── login_page.py
│       ├── main_page.py
│       ├── logger.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── Dockerfile
├── .dockerignore
├── pyproject.toml
└── README.md
```

## 本地运行

```bash
# 运行命令行版本
python -m src.brain_lit.main

# 运行Streamlit Web应用
streamlit run src/brain_lit/app.py
```

## 运行测试

```bash
# 直接运行测试文件
python tests/test_main.py
```

## Docker支持

构建镜像：

```bash
docker build -t brain-lit .
```

运行容器：

```bash
# 运行命令行版本
docker run brain-lit

# 运行Streamlit Web应用
docker run -p 8501:8501 brain-lit
```

## 项目特点

- 使用现代Python项目结构（src布局）
- 支持通过Docker容器化部署
- 包含基础测试框架
- 使用pyproject.toml进行项目配置和依赖管理
- Docker构建中使用[uv](https://github.com/astral-sh/uv)加速依赖安装
- 集成日志系统，日志信息包含模块名和代码行号
- 提供基于Streamlit的Web界面，包含登录功能