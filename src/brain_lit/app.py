import os
import sys

import streamlit as st

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main_page import render_main_page
from brain_lit.logger import setup_logger

# 设置logger
logger = setup_logger(__name__)

def main():
    """主应用函数"""
    # logger.info("********** Before main() called，当前st.session_state内容:")
    # for key, value in st.session_state.items():
    #     logger.info(f"- {key}: {value}")

    render_main_page()

if __name__ == "__main__":
    main()