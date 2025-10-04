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
    render_main_page()

if __name__ == "__main__":
    main()