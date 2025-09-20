import streamlit as st
import sys
import os

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from login_page import render_login_page
from main_page import render_main_page
from brain_lit.svc.auth import AutoLoginSession

# 设置页面配置
st.set_page_config(
    page_title="Brain-Lit Application",
    page_icon="🧠",
    layout="centered"
)

# 初始化会话状态
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    
if 'username' not in st.session_state:
    st.session_state.username = ""

# 创建全局AutoLoginSession实例
if 'global_session' not in st.session_state:
    st.session_state.global_session = AutoLoginSession()

def main():
    """主应用函数"""
    if not st.session_state.logged_in:
        render_login_page()
    else:
        render_main_page()

if __name__ == "__main__":
    main()