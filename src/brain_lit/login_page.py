import streamlit as st
import time
import sys
import os

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def validate_credentials(username, password):
    """验证用户凭据（通过实际API调用）"""
    try:
        # 使用全局session实例
        session = st.session_state.global_session
        session.login_with_credentials(username, password)
        user_id = session.user_id
        return True, user_id
    except Exception as e:
        print(f"登录验证失败: {e}")
        return False, None

def render_login_page():
    """显示登录页面"""
    st.title("🧠 Brain-Lit 登录")
    st.markdown("请登录以访问应用程序")
    
    # 从浏览器存储中获取保存的用户名和密码
    saved_username = st.session_state.get('saved_username', '')
    saved_password = st.session_state.get('saved_password', '')
    
    # 登录表单
    with st.form("login_form"):
        username = st.text_input("用户名", value=saved_username)
        password = st.text_input("密码", type="password", value=saved_password)
        remember_me = st.checkbox("记住我", value=bool(saved_username and saved_password))
        
        submitted = st.form_submit_button("登录")
        
        if submitted:
            if username and password:
                # 验证登录凭据
                with st.spinner("正在验证凭据..."):
                    is_valid, user_id = validate_credentials(username, password)
                
                if is_valid:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_id = user_id
                    # 保存登录时间
                    st.session_state.login_time = time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 如果用户选择记住凭据，则保存到会话状态
                    if remember_me:
                        st.session_state.saved_username = username
                        st.session_state.saved_password = password
                    else:
                        # 如果用户取消记住，则清除保存的凭据
                        st.session_state.saved_username = ""
                        st.session_state.saved_password = ""
                    
                    st.success("登录成功！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
            else:
                st.warning("请输入用户名和密码")