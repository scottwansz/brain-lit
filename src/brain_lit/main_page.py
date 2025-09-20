import streamlit as st
import time
import sys
import os
import logging
import streamlit_js_eval

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brain_lit.logger import setup_logger

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

def render_main_page():
    """显示主页面"""
    # 记录调试信息到日志
    logger.info("当前会话状态:")
    logger.info(f"- logged_in: {st.session_state.get('logged_in', 'Not set')}")
    logger.info(f"- username: {st.session_state.get('username', 'Not set')}")
    logger.info(f"- user_id: {st.session_state.get('user_id', 'Not set')}")
    logger.info(f"- saved_username: {st.session_state.get('saved_username', 'Not set')}")
    logger.info(f"- saved_password是否存在: {bool(st.session_state.get('saved_password', ''))}")
    logger.info(f"- login_time: {st.session_state.get('login_time', 'Not set')}")
    
    # 使用全局会话对象以获取登录信息
    session = st.session_state.global_session
    time_until_expiry = session.get_time_until_expiry()
    formatted_time = format_time_remaining(time_until_expiry)
    
    # 显示用户信息和退出按钮的侧边栏
    with st.sidebar:
        st.title(f"欢迎, {st.session_state.username}!")
        st.markdown("---")
        st.markdown("### 用户信息")
        st.markdown(f"**用户名:** {st.session_state.username}")
        st.markdown(f"**用户ID:** {st.session_state.get('user_id', 'Unknown')}")
        # 使用存储在会话状态中的实际登录时间
        st.markdown(f"**登录时间:** {st.session_state.get('login_time', 'Unknown')}")
        
        st.markdown("---")
        st.markdown("### 登录状态")
        st.markdown(f"**登录即将失效:** {formatted_time}")
        
        # 添加一个刷新按钮来更新剩余时间
        if st.button("刷新状态"):
            st.rerun()
        
        st.markdown("---")
        if st.button("退出登录"):
            # 调用session的logout方法
            session.logout()
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user_id = ""
            # 清除保存的凭据
            if 'saved_username' in st.session_state:
                del st.session_state.saved_username
            if 'saved_password' in st.session_state:
                del st.session_state.saved_password
            if 'login_time' in st.session_state:
                del st.session_state.login_time
            # 同时清除浏览器存储的凭据
            try:
                streamlit_js_eval.set_cookie("brain_lit_credentials", "", -1)  # 删除cookie
                logger.info("已从浏览器cookie清除凭据")
            except Exception as e:
                logger.error(f"从浏览器清除凭据时出错: {e}")
            st.success("已退出登录")
            time.sleep(1)
            st.rerun()
    
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
    
    st.markdown("### 使用说明")
    st.markdown("""
    1. 在左侧边栏查看用户信息
    2. 使用顶部导航访问不同功能
    3. 点击"退出登录"按钮安全退出
    """)
    
    # 显示登录状态信息
    st.markdown("### 当前登录状态")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("用户ID", st.session_state.get('user_id', 'Unknown'))
    with col2:
        st.metric("登录剩余时间", formatted_time)