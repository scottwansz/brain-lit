import streamlit as st
import time
import sys
import os
import logging
import streamlit_js_eval

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brain_lit.logger import setup_logger
from brain_lit.sidebar import render_sidebar

# 设置logger
logger = setup_logger()

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

def clear_session_from_browser():
    """从浏览器清除AutoLoginSession对象"""
    try:
        streamlit_js_eval.set_cookie("brain_lit_session", "", -1)  # 删除cookie
        logger.info("已从浏览器cookie清除AutoLoginSession")
    except Exception as e:
        logger.error(f"从浏览器清除AutoLoginSession时出错: {e}")

def render_main_page():
    """显示主页面"""
    # 记录调试信息到日志
    # logger.info("当前会话状态:")
    # logger.info(f"- logged_in: {st.session_state.get('logged_in', 'Not set')}")
    # logger.info(f"- username: {st.session_state.get('username', 'Not set')}")
    # logger.info(f"- user_id: {st.session_state.get('user_id', 'Not set')}")
    # logger.info(f"- saved_username: {st.session_state.get('saved_username', 'Not set')}")
    # logger.info(f"- saved_password是否存在: {bool(st.session_state.get('saved_password', ''))}")
    # logger.info(f"- login_time: {st.session_state.get('login_time', 'Not set')}")
    
    # 检查用户是否仍然登录
    # if not st.session_state.get('logged_in', False):
    #     # 如果用户未登录，不应该显示主页面
    #     from brain_lit.login_page import render_login_page
    #     render_login_page()
    #     st.stop()  # 添加这行确保立即停止执行并跳转
    #     return
    
    # 渲染共享的侧边栏
    render_sidebar()
    
    # 使用全局会话对象以获取登录信息
    session = st.session_state.global_session
    time_until_expiry = session.get_time_until_expiry()
    formatted_time = format_time_remaining(time_until_expiry)
    
    # 主页面内容
    st.title("🧠 Brain-Lit 应用")
    st.markdown("欢迎使用 Brain-Lit 应用程序！")
    
    st.markdown("### 功能列表")
    st.markdown("""
    - 数据分析
    - 可视化展示
    - 报告生成
    - 模型训练
    """)
    
    st.markdown("### Alpha工作流程")
    st.markdown("""
    1. **生成Alpha**: 编写Alpha表达式
    2. **Simulate Alpha**: 对Alpha进行回测模拟
    3. **提交Alpha**: 提交验证后的Alpha
    """)
    
    # 显示登录状态信息
    st.markdown("### 当前登录状态")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("用户ID", session.user_id)
    with col2:
        st.metric("登录剩余时间", formatted_time)