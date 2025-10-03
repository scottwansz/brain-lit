import os
import sys

import streamlit as st

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main_page import render_main_page
from brain_lit.logger import setup_logger

# 设置logger
logger = setup_logger()

def main():
    """主应用函数"""
    import pandas as pd

    # 您的数据
    data = [{'simulated': '1', 'count': 93}, {'simulated': '-1', 'count': 30}]

    # 转换为DataFrame
    df = pd.DataFrame(data)

    # 显示条形图，使用simulated列作为颜色分组
    st.bar_chart(df, x="simulated", y="count", color="simulated", horizontal=True)

    render_main_page()

if __name__ == "__main__":
    main()