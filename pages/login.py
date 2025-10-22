import base64
import json
import os
import sys
import time

import streamlit as st
import streamlit_js_eval

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from svc.logger import setup_logger

# 设置logger
logger = setup_logger(__name__)

def validate_credentials(username, password):
    """验证用户凭据（通过实际API调用）"""
    try:
        # 使用全局session实例
        session = st.session_state.global_session
        session.login_with_credentials(username, password)
        user_id = session.user_id
        return True, user_id
    except Exception as e:
        logger.error(f"登录验证失败: {e}")
        return False, None

def save_session_to_browser():
    """将AutoLoginSession对象保存到浏览器"""
    try:
        session = st.session_state.global_session
        if session.username and session.password:
            credentials = {
                'username': session.username,
                'password': base64.b64encode(session.password.encode()).decode(),
                'user_id': session.user_id,
                'last_login_time': session.last_login_time,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            credentials_json = json.dumps(credentials)
            streamlit_js_eval.set_cookie("brain_lit_session", credentials_json, 30)  # 30天有效期
            logger.info("AutoLoginSession已保存到浏览器cookie")
    except Exception as e:
        logger.error(f"保存AutoLoginSession到浏览器时出错: {e}")

def clear_session_from_browser():
    """从浏览器清除AutoLoginSession对象"""
    try:
        streamlit_js_eval.set_cookie("brain_lit_session", "", -1)  # 删除cookie
        logger.info("已从浏览器cookie清除AutoLoginSession")
    except Exception as e:
        logger.error(f"从浏览器清除AutoLoginSession时出错: {e}")

def render_login_page():
    """显示登录页面"""
    st.title("🧠 Brain-Lit 登录")
    st.markdown("请登录以访问应用程序")
    
    # 登录表单
    with st.form("login_form"):
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        remember_me = st.checkbox("记住我", value=True)
        
        submitted = st.form_submit_button("登录")
        
        if submitted:
            logger.info(f"提交表单，用户名={username}, 记住我={remember_me}")
            if username and password:
                # 验证登录凭据
                with st.spinner("正在验证凭据..."):
                    is_valid, user_id = validate_credentials(username, password)
                
                if is_valid:
                    logger.info(f"登录验证成功，用户ID={user_id}")
                    
                    # 如果用户选择了"记住我"，则保存session到浏览器
                    if remember_me:
                        logger.info(f"保存AutoLoginSession到浏览器")
                        save_session_to_browser()
                    else:
                        # 如果未选择记住我，则清除已保存的session
                        logger.info("未选择记住我，清除已保存的session")
                        clear_session_from_browser()
                    
                    # 重新运行应用以显示主页面
                    st.rerun()
                else:
                    st.error("登录失败，请检查用户名和密码")
            else:
                st.warning("请输入用户名和密码")

    # 添加说明信息
    st.info("提示：选择'记住我'可以在下次访问时自动登录")