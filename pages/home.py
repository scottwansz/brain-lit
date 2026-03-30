import os
import sys

import streamlit as st

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from svc.logger import setup_logger

# 设置logger
logger = setup_logger(__name__)

def format_time_remaining(seconds):
    """格式化剩余时间显示"""
    if seconds <= 0:
        return "已过期"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{int(hours)}小时{int(minutes)}分钟{int(secs)}秒"
    elif minutes > 0:
        return f"{int(minutes)}分钟{int(secs)}秒"
    else:
        return f"{int(secs)}秒"

def render_main_page():
    """显示主页面"""
    
    # 主页面内容
    st.title("🧠 Brain-Lit 应用")
    st.markdown("欢迎使用 Brain-Lit 应用程序！")
    
    st.markdown("### Alpha工作流程")
    st.markdown("""
    1. **生成Alpha**: 选择数据集与模板生成Alpha表达式
    2. **Simulate Alpha**: 对Alpha进行回测模拟
    3. **提交Alpha**: 提交验证后的Alpha
    """)