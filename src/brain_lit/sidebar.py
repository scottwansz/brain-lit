import streamlit as st
import logging
from brain_lit.logger import setup_logger

# 设置logger
logger = setup_logger()

def render_sidebar():
    """渲染共享的侧边栏"""
    # 检查用户是否仍然登录
    if not st.session_state.get('logged_in', False):
        st.switch_page("app.py")
        return
    
    with st.sidebar:
        st.title(f"欢迎, {st.session_state.get('user_id', 'Unknown')}!")
        st.markdown(f"**登录时间:** {st.session_state.get('login_time', 'Unknown')}")
        st.markdown("---")
        st.markdown("### 页面导航")
        if st.button("🏠 主页"):
            st.switch_page("app.py")
        if st.button("📈 生成Alpha"):
            st.switch_page("pages/1_alpha_generate.py")
        if st.button("🔬 Simulate Alpha"):
            st.switch_page("pages/2_alpha_simulate.py")
        if st.button("📤 提交Alpha"):
            st.switch_page("pages/3_alpha_submit.py")
        
        st.markdown("---")
        if st.button("🚪 退出登录"):
            _handle_logout()
        
def _handle_logout():
    """处理退出登录逻辑"""
    try:
        # 调用session的logout方法
        session = st.session_state.global_session
        session.logout()
        
        # 清除会话状态
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_id = ""
        
        # 清除保存的凭据
        keys_to_remove = ['saved_username', 'saved_password', 'login_time', 'current_page', 'pending_alpha']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        
        # 清除浏览器存储的session
        try:
            import streamlit_js_eval
            streamlit_js_eval.set_cookie("brain_lit_session", "", -1)  # 删除cookie
            logger.info("已从浏览器cookie清除AutoLoginSession")
        except Exception as e:
            logger.error(f"从浏览器清除AutoLoginSession时出错: {e}")
            
        st.success("已退出登录")
        st.switch_page("app.py")
    except Exception as e:
        logger.error(f"退出登录时发生错误: {e}")
        st.error("退出登录时发生错误，请重新尝试")