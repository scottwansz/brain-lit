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

st.title("🔬 Simulate Alpha")

# 获取待处理的Alpha表达式
pending_alpha = st.session_state.get('pending_alpha', '')

# 主要内容区域
st.markdown("在本页面您可以对Alpha表达式进行模拟回测。")

# 显示Alpha表达式
st.subheader("Alpha表达式")
if pending_alpha:
    st.code(pending_alpha, language="python")
else:
    st.info("暂无待模拟的Alpha表达式")

# 模拟回测参数
st.subheader("回测参数")
col1, col2, col3 = st.columns(3)

with col1:
    start_date = st.date_input("开始日期", value=None)
    region = st.selectbox("地区", ["USA", "CHN", "EU", "JP", "KR"])

with col2:
    end_date = st.date_input("结束日期", value=None)
    universe = st.selectbox("股票池", ["TOP500", "TOP1000", "TOP2000", "ALL"])

with col3:
    initial_capital = st.number_input("初始资金", min_value=10000, value=1000000)
    transaction_cost = st.slider("交易成本(%)", 0.0, 1.0, 0.1, 0.01)

# 模拟回测结果
st.subheader("回测结果")

# 检查是否正在进行模拟
if 'simulation_running' not in st.session_state:
    st.session_state.simulation_running = False

# 操作按钮
col4, col5, col6 = st.columns([1, 1, 4])

with col4:
    if st.button("开始模拟", type="primary"):
        if pending_alpha:
            st.session_state.simulation_running = True
            st.rerun()
        else:
            st.warning("没有待模拟的Alpha表达式")

with col5:
    if st.button("提交Alpha"):
        st.switch_page("pages/3_提交_Alpha.py")

# 显示模拟进度或结果
if st.session_state.simulation_running:
    # 模拟进度条
    progress_text = "正在进行回测模拟，请稍候..."
    my_bar = st.progress(0, text=progress_text)
    
    for percent_complete in range(100):
        time.sleep(0.01)  # 模拟计算时间
        my_bar.progress(percent_complete + 1, text=progress_text)
    
    st.session_state.simulation_running = False
    st.success("模拟完成！")
    
    # 显示模拟结果
    st.markdown("### 绩效指标")
    col7, col8, col9, col10 = st.columns(4)
    
    with col7:
        st.metric("年化收益", f"{random.uniform(5.0, 25.0):.2f}%")
    
    with col8:
        st.metric("最大回撤", f"{random.uniform(5.0, 15.0):.2f}%")
    
    with col9:
        st.metric("夏普比率", f"{random.uniform(0.5, 2.0):.2f}")
    
    with col10:
        st.metric("胜率", f"{random.uniform(50.0, 70.0):.2f}%")
    
    # 图表展示
    st.markdown("### 收益曲线")
    chart_data = {
        "时间": ["1月", "2月", "3月", "4月", "5月", "6月"],
        "累计收益": [100, 105, 112, 108, 115, 122],
        "基准收益": [100, 102, 104, 106, 108, 110]
    }
    st.line_chart(chart_data, x="时间", y=["累计收益", "基准收益"])
    
    # 详细结果
    with st.expander("查看详细结果"):
        st.markdown("""
        ### 回测详情
        - **总交易次数**: 127
        - **平均持仓天数**: 5.3
        - **换手率**: 245.6%
        - **信息比率**: 1.27
        - **Calmar比率**: 0.89
        """)