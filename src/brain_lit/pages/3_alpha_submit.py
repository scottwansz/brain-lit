import streamlit as st
import sys
import os
import time
import random

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brain_lit.logger import setup_logger
from brain_lit.sidebar import render_sidebar

# 设置logger
logger = setup_logger()

# 渲染共享的侧边栏
render_sidebar()

st.title("📤 提交Alpha")

# 获取待处理的Alpha表达式
pending_alpha = st.session_state.get('pending_alpha', '')

# 主要内容区域
st.markdown("在本页面您可以提交经过验证的Alpha表达式。")

# 显示Alpha表达式
st.subheader("待提交的Alpha表达式")
if pending_alpha:
    st.code(pending_alpha, language="python")
else:
    st.info("暂无待提交的Alpha表达式")

# 提交信息
st.subheader("提交信息")
alpha_name = st.text_input("Alpha名称", placeholder="给您的Alpha起个名字")
alpha_description = st.text_area("Alpha描述", placeholder="简要描述您的Alpha策略逻辑", height=100)

# 提交设置
st.subheader("提交设置")
col1, col2 = st.columns(2)

with col1:
    visibility = st.radio("可见性", ["私有", "团队可见", "公开"], index=0)
    tags = st.multiselect("标签", ["价值", "动量", "质量", "波动率", "量价"], default=[])

with col2:
    commission_type = st.selectbox("佣金类型", ["标准", "优惠", "免费"])
    expected_sharpe = st.number_input("预期夏普比率", min_value=0.0, max_value=5.0, value=1.0, step=0.1)

# 操作按钮
st.markdown("---")
col3, col4, col5 = st.columns([1, 1, 4])

with col3:
    if st.button("提交Alpha", type="primary"):
        if pending_alpha and alpha_name:
            # 模拟提交过程
            with st.spinner("正在提交Alpha..."):
                time.sleep(2)  # 模拟提交时间
            
            # 生成模拟提交ID
            submission_id = f"ALPHA-{random.randint(10000, 99999)}"
            st.success(f"Alpha提交成功！提交ID: {submission_id}")
            
            # 清除pending alpha
            if 'pending_alpha' in st.session_state:
                del st.session_state.pending_alpha
            
            st.info("您可以在Alpha管理页面查看提交状态")
        elif not alpha_name:
            st.warning("请输入Alpha名称")
        else:
            st.warning("没有待提交的Alpha表达式")

with col4:
    if st.button("重新编辑"):
        st.switch_page("pages/1_生成_Alpha.py")

# 提交历史
st.markdown("---")
st.subheader("提交历史")

# 模拟提交历史数据
if 'submission_history' not in st.session_state:
    st.session_state.submission_history = [
        {"id": "ALPHA-12345", "name": "价值因子Alpha", "date": "2025-09-15", "status": "已接受"},
        {"id": "ALPHA-67890", "name": "动量反转策略", "date": "2025-09-10", "status": "审核中"},
    ]

for submission in st.session_state.submission_history:
    status_color = "green" if submission["status"] == "已接受" else "orange"
    st.markdown(f"""
    <div style="border: 1px solid #e0e0e0; border-radius: 5px; padding: 10px; margin-bottom: 10px;">
        <div style="display: flex; justify-content: space-between;">
            <div><b>{submission['name']}</b> ({submission['id']})</div>
            <div style="color: {status_color};"><b>{submission['status']}</b></div>
        </div>
        <div>提交日期: {submission['date']}</div>
    </div>
    """, unsafe_allow_html=True)