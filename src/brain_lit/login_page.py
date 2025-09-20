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

def render_login_page():
    """显示登录页面"""
    st.title("🧠 Brain-Lit 登录")
    st.markdown("请登录以访问应用程序")
    
    # 记录调试信息到日志
    logger.info("当前会话状态:")
    logger.info(f"- logged_in: {st.session_state.get('logged_in', 'Not set')}")
    logger.info(f"- saved_username: {st.session_state.get('saved_username', 'Not set')}")
    logger.info(f"- saved_password是否存在: {bool(st.session_state.get('saved_password', ''))}")
    
    # 从st.session_state中获取保存的用户名和密码
    saved_username = st.session_state.get('saved_username', '')
    saved_password = st.session_state.get('saved_password', '')
    
    # 登录表单
    with st.form("login_form"):
        username = st.text_input("用户名", value=saved_username)
        password = st.text_input("密码", type="password", value=saved_password)
        remember_me = st.checkbox("记住我", value=bool(saved_username and saved_password))
        
        submitted = st.form_submit_button("登录")
        
        if submitted:
            logger.info(f"提交表单，用户名={username}, 记住我={remember_me}")
            if username and password:
                # 验证登录凭据
                with st.spinner("正在验证凭据..."):
                    is_valid, user_id = validate_credentials(username, password)
                
                if is_valid:
                    logger.info(f"登录验证成功，用户ID={user_id}")
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_id = user_id
                    # 保存登录时间
                    st.session_state.login_time = time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 如果用户选择了"记住我"，则保存凭据到浏览器
                    if remember_me:
                        logger.info(f"保存凭据，用户名={username}")
                        st.session_state.saved_username = username
                        st.session_state.saved_password = password
                        # 保存到浏览器cookie
                        try:
                            import json
                            import base64
                            credentials = {
                                'username': username,
                                'password': base64.b64encode(password.encode()).decode(),
                                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                            }
                            credentials_json = json.dumps(credentials)
                            streamlit_js_eval.set_cookie("brain_lit_credentials", credentials_json, 30)  # 30天有效期
                            logger.info("凭据已保存到浏览器cookie")
                        except Exception as e:
                            logger.error(f"保存凭据到浏览器时出错: {e}")
                    else:
                        # 如果未选择记住我，则清除已保存的凭据
                        logger.info("未选择记住我，清除已保存的凭据")
                        if 'saved_username' in st.session_state:
                            del st.session_state.saved_username
                        if 'saved_password' in st.session_state:
                            del st.session_state.saved_password
                        # 同时清除浏览器存储的凭据
                        try:
                            streamlit_js_eval.set_cookie("brain_lit_credentials", "", -1)  # 删除cookie
                            logger.info("已从浏览器cookie清除凭据")
                        except Exception as e:
                            logger.error(f"从浏览器清除凭据时出错: {e}")
                    
                    # 重新运行应用以显示主页面
                    st.rerun()
                else:
                    st.error("登录失败，请检查用户名和密码")
            else:
                st.warning("请输入用户名和密码")

    # 添加说明信息
    st.info("提示：选择'记住我'可以在下次访问时自动填充用户名和密码")