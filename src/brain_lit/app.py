import streamlit as st
import sys
import os
import time
import json
import base64
import streamlit_js_eval
from datetime import datetime, timedelta

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from login_page import render_login_page
from main_page import render_main_page
from brain_lit.svc.auth import AutoLoginSession
from brain_lit.logger import setup_logger

# 设置logger
logger = setup_logger()

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

def save_session_to_browser():
    """将AutoLoginSession对象保存到浏览器localStorage"""
    try:
        session = st.session_state.global_session
        if session.username and session.password:
            # 将凭据和用户ID编码后保存到localStorage
            credentials = {
                'username': session.username,
                'password': base64.b64encode(session.password.encode()).decode(),
                'user_id': session.user_id,
                'last_login_time': session.last_login_time,
                'timestamp': datetime.now().isoformat()
            }
            credentials_json = json.dumps(credentials)
            streamlit_js_eval.set_cookie("brain_lit_session", credentials_json, 30)  # 30天有效期
            logger.info(f"AutoLoginSession已保存到浏览器cookie: {session.username}")
    except Exception as e:
        logger.error(f"保存AutoLoginSession到浏览器时出错: {e}")

def load_session_from_browser():
    """从浏览器localStorage加载AutoLoginSession对象"""
    try:
        # 从cookie中获取凭据
        credentials_json = streamlit_js_eval.get_cookie("brain_lit_session")

        # 等待JavaScript环境完全加载，确保能正确读取cookie
        time.sleep(0.1)

        logger.info(f"从浏览器cookie获取到的凭据: {credentials_json}")
        if credentials_json:
            credentials = json.loads(credentials_json)
            username = credentials.get('username', '')
            password_encoded = credentials.get('password', '')
            user_id = credentials.get('user_id', '')
            last_login_time = credentials.get('last_login_time', 0)
            if username and password_encoded:
                password = base64.b64decode(password_encoded.encode()).decode()
                logger.info(f"从浏览器cookie加载AutoLoginSession: {username}")
                return username, password, user_id, last_login_time
        return None, None, None, 0
    except Exception as e:
        logger.error(f"从浏览器加载AutoLoginSession时出错: {e}")
        return None, None, None, 0

def clear_session_from_browser():
    """从浏览器localStorage清除AutoLoginSession对象"""
    try:
        streamlit_js_eval.set_cookie("brain_lit_session", "", -1)  # 删除cookie
        logger.info("已从浏览器cookie清除AutoLoginSession")
    except Exception as e:
        logger.error(f"从浏览器清除AutoLoginSession时出错: {e}")

def try_auto_login():
    """尝试自动登录"""
    logger.info("开始尝试自动登录...")
    
    # 等待JavaScript环境完全加载，确保能正确读取cookie
    time.sleep(0.1)
    
    # 获取全局session实例
    session = st.session_state.global_session
    
    # 检查session中是否已经保存了用户名和密码
    if session.username and session.password:
        logger.info(f"在AutoLoginSession中发现保存的凭据，用户名: {session.username}")
        try:
            # 尝试确保会话有效
            session.ensure_valid_session()
            if session.user_id:
                st.session_state.logged_in = True
                st.session_state.username = session.username
                st.session_state.user_id = session.user_id
                # 如果登录时间不存在，则根据last_login_time设置或使用当前时间
                if 'login_time' not in st.session_state:
                    if session.last_login_time:
                        st.session_state.login_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session.last_login_time))
                    else:
                        st.session_state.login_time = time.strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"通过AutoLoginSession自动登录成功，用户ID: {session.user_id}")
                return True
        except Exception as e:
            logger.error(f"通过AutoLoginSession自动登录失败: {e}")
    
    # 如果AutoLoginSession中没有凭据或登录失败，尝试从浏览器存储加载
    saved_username, saved_password, saved_user_id, saved_last_login_time = load_session_from_browser()

    logger.info(f"保存的用户名={saved_username}, 保存的密码是否存在={bool(saved_password)}, 保存的用户ID={saved_user_id}")
    
    # 如果有保存的凭据，尝试自动登录
    if saved_username and saved_password:
        logger.info("发现保存的凭据，正在尝试自动登录...")
        try:
            session = st.session_state.global_session
            # 如果从浏览器恢复的会话包含用户ID，则直接使用
            if saved_user_id:
                session.username = saved_username
                session.password = saved_password
                session.user_id = saved_user_id
                session.last_login_time = saved_last_login_time
                st.session_state.logged_in = True
                st.session_state.username = saved_username
                st.session_state.user_id = saved_user_id
                # 如果登录时间不存在，则根据last_login_time设置或使用当前时间
                if 'login_time' not in st.session_state:
                    if saved_last_login_time:
                        st.session_state.login_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(saved_last_login_time))
                    else:
                        st.session_state.login_time = time.strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"从浏览器恢复会话成功，用户ID: {session.user_id}")
                return True
            else:
                # 否则执行完整登录流程
                session.login_with_credentials(saved_username, saved_password)
                st.session_state.logged_in = True
                st.session_state.username = saved_username
                st.session_state.user_id = session.user_id
                # 如果登录时间不存在，则根据last_login_time设置或使用当前时间
                if 'login_time' not in st.session_state:
                    st.session_state.login_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session.last_login_time))
                logger.info("自动登录成功")
                return True
        except Exception as e:
            # 自动登录失败，清除保存的凭据
            st.session_state.logged_in = False
            clear_session_from_browser()  # 同时清除浏览器存储的凭据
            logger.error(f"自动登录失败: {e}")
            return False
    else:
        logger.info("没有找到保存的凭据")
    return False

def main():
    """主应用函数"""
    try_auto_login()

    # 应用启动时检查自动登录
    logger.info("应用启动，当前st.session_state内容:")
    for key, value in st.session_state.items():
        logger.info(f"- {key}: {value}")

    if not st.session_state.logged_in:
        render_login_page()
        st.stop()  # 添加这行确保立即停止执行并跳转
    else:
        render_main_page()

if __name__ == "__main__":
    main()