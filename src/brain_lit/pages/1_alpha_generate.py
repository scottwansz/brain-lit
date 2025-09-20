import streamlit as st
import sys
import os

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brain_lit.logger import setup_logger
from brain_lit.sidebar import render_sidebar

# 设置logger
logger = setup_logger()

# 渲染共享的侧边栏
render_sidebar()

st.title("📈 生成Alpha")

# 主要内容区域
st.markdown("在本页面您可以生成新的Alpha表达式。")

# Alpha表达式输入区域
st.subheader("Alpha表达式")
alpha_expression = st.text_area(
    "请输入您的Alpha表达式:",
    height=200,
    placeholder="# 示例Alpha表达式\n# rank(correlation(close, returns, 5))"
)

# 参数设置
st.subheader("参数设置")
col1, col2, col3 = st.columns(3)

with col1:
    start_date = st.date_input("开始日期", value=None)
    region = st.selectbox("地区", ["USA", "CHN", "EU", "JP", "KR"])

with col2:
    end_date = st.date_input("结束日期", value=None)
    universe = st.selectbox("股票池", ["TOP500", "TOP1000", "TOP2000", "ALL"])

with col3:
    decay = st.number_input("衰减天数", min_value=1, max_value=30, value=5)
    delay = st.number_input("延迟天数", min_value=0, max_value=10, value=1)

# 其他设置
st.subheader("其他设置")
col4, col5 = st.columns(2)

with col4:
    neutralization = st.multiselect(
        "中性化选项",
        ["SIZE", "SECTOR", "VOLATILITY", "LIQUIDITY", "MOMENTUM"],
        default=["SIZE", "SECTOR"]
    )

with col5:
    truncation = st.slider("截断百分比", 0.0, 10.0, 5.0, 0.1)
    pasteurization = st.checkbox("Pasteurization", value=True)

# 操作按钮
st.markdown("---")
col6, col7, col8 = st.columns([1, 1, 4])

with col6:
    if st.button("生成Alpha", type="primary"):
        if alpha_expression.strip():
            st.success("Alpha表达式已提交进行回测！")
            st.session_state.pending_alpha = alpha_expression
            st.switch_page("pages/2_Simulate_Alpha.py")
        else:
            st.warning("请输入Alpha表达式")

with col7:
    if st.button("清空"):
        st.rerun()

# 显示示例
with st.expander("查看Alpha表达式示例"):
    st.markdown("""
    ### 常用函数示例:
    - `rank(correlation(close, returns, 5))`
    - `ts_mean(volume, 10) / ts_mean(volume, 30)`
    - `zscore(open / close)`
    
    ### 可用操作符:
    - 基本运算: `+`, `-`, `*`, `/`, `**`
    - 比较运算: `<`, `>`, `<=`, `>=`, `==`, `!=`
    - 逻辑运算: `&` (与), `|` (或), `~` (非)
    """)