import base64
import json
import os
import sys
import time

import streamlit as st
import streamlit_js_eval

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from login_page import render_login_page
from main_page import render_main_page
from brain_lit.svc.auth import AutoLoginSession
from brain_lit.logger import setup_logger

# 设置logger
logger = setup_logger()

def main():
    """主应用函数"""
    render_main_page()
    # logger.info("********** Before main() called，当前st.session_state内容:")
    # for key, value in st.session_state.items():
    #     logger.info(f"- {key}: {value}")

    # # 创建全局AutoLoginSession实例
    # if 'global_session' not in st.session_state:
    #     # logger.info("get_cookie brain_lit_session")
    #
    #     streamlit_js_eval.get_cookie("brain_lit_session")
    #     time.sleep(0.1)
    #
    #     if st.session_state.getCookie_brain_lit_session:
    #
    #         stored_session = json.loads(st.session_state.getCookie_brain_lit_session)
    #         logger.info('st.session_state.getCookie_brain_lit_session: %s', stored_session)
    #
    #         username = stored_session.get('username')
    #         password = base64.b64decode(stored_session.get('password').encode()).decode()
    #
    #         st.session_state.global_session = AutoLoginSession(username, password)
    #
    #     else:
    #         st.session_state.global_session = AutoLoginSession()
    #
    # logger.info("********** After main() called，当前st.session_state内容:")
    # for key, value in st.session_state.items():
    #     logger.info(f"- {key}: {value}")

    # if st.session_state.global_session.user_id:
    #     logger.info("render_main_page")
    #     render_main_page()
    # else:
    #     logger.info("render_login_page")
    #     render_login_page()
    #     st.stop()  # 添加这行确保立即停止执行并跳转

if __name__ == "__main__":
    main()