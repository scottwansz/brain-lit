import streamlit as st
import sys
import os

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brain_lit.logger import setup_logger
from brain_lit.sidebar import render_sidebar
from brain_lit.svc.dataset import get_dataset_list

# 设置logger
logger = setup_logger()

# 渲染共享的侧边栏
render_sidebar()

st.title("📈 生成Alpha")

# 主要内容区域
st.markdown("在本页面您可以生成新的Alpha表达式。")

# 初始化session state中的参数
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

# 从session state获取已选择的参数
selected_region = st.session_state.selected_region
selected_universe = st.session_state.selected_universe
selected_delay = st.session_state.selected_delay
selected_category = st.session_state.selected_category

# 数据集选择部分
st.subheader("数据集选择")

# 当参数发生变化时重置页码
params_changed = (
    selected_region != st.session_state.get('prev_region', selected_region) or 
    selected_universe != st.session_state.get('prev_universe', selected_universe) or 
    selected_delay != st.session_state.get('prev_delay', selected_delay) or
    selected_category != st.session_state.get('prev_category', selected_category)
)

if params_changed:
    st.session_state.current_page = 1

# 保存当前参数以便下次比较
st.session_state.prev_region = selected_region
st.session_state.prev_universe = selected_universe
st.session_state.prev_delay = selected_delay
st.session_state.prev_category = selected_category

# 分页显示数据集
session = st.session_state.global_session

# 构建API请求参数
dataset_params = {
    "region": selected_region,
    "universe": selected_universe,
    "delay": selected_delay,
    "instrumentType": "EQUITY",
    "limit": 20,
    "offset": (st.session_state.current_page - 1) * 20,
}

# 添加分类参数（如果不是"All"）
if selected_category:
    dataset_params["category"] = selected_category

# 获取数据集列表
with st.spinner("正在获取数据集列表..."):
    dataset_response = get_dataset_list(session, dataset_params)
datasets = dataset_response.get("results", [])
total_count = dataset_response.get("count", 0)

# 显示数据集选择
if datasets:
    # 计算总页数
    page_size = 10
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
    
    # 确保当前页码在有效范围内
    if st.session_state.current_page > total_pages:
        st.session_state.current_page = total_pages
    if st.session_state.current_page < 1:
        st.session_state.current_page = 1
    
    # 在同一行显示数据集总数和分页控件
    count_col, _, prev_col, info_col, next_col = st.columns([3, 1, 1, 2, 1])
    with count_col:
        st.write(f"共找到 {total_count} 个数据集")
    with prev_col:
        if st.button("上一页", disabled=(st.session_state.current_page <= 1)):
            st.session_state.current_page -= 1
            st.rerun()
    with info_col:
        st.write(f"第 {st.session_state.current_page} 页，共 {total_pages} 页")
    with next_col:
        if st.button("下一页", disabled=(st.session_state.current_page >= total_pages)):
            st.session_state.current_page += 1
            st.rerun()
    
    # 显示表格形式的数据集
    # 创建表格标题行
    header_cols = st.columns([1, 2, 2, 1, 1, 1, 1, 1, 1, 1])
    headers = ["选择", "ID", "分类", "主题乘数", "覆盖率", "价值评分", "用户数", "Alpha数", "字段数", "金字塔乘数"]
    
    for col, header in zip(header_cols, headers):
        col.write(f"**{header}**")
    
    # 显示数据行
    for dataset in datasets:
        # 处理themes字段，显示multiplier值而不是name值
        themes_multiplier = ", ".join([str(theme.get("multiplier", "")) for theme in dataset.get("themes", [])]) if dataset.get("themes") else ""
        
        # 创建数据行
        cols = st.columns([1, 2, 2, 1, 1, 1, 1, 1, 1, 1])
        
        # 复选框
        with cols[0]:
            dataset_id = dataset.get("id", "")
            is_selected = st.checkbox(
                f"选择数据集 {dataset_id}", 
                key=f"select_{dataset_id}",
                value=st.session_state.get(f"selected_dataset_{dataset_id}", False),
                label_visibility="collapsed"
            )
            # 更新session state
            if is_selected:
                st.session_state[f"selected_dataset_{dataset_id}"] = dataset
            elif f"selected_dataset_{dataset_id}" in st.session_state:
                del st.session_state[f"selected_dataset_{dataset_id}"]
        
        # 数据列
        cols[1].write(dataset_id)
        cols[2].write(f"{dataset.get('category', {}).get('name', '')}")
        cols[3].write(themes_multiplier)
        cols[4].write(f"{dataset.get('coverage', 0):.2%}")
        cols[5].write(dataset.get("valueScore", 0))
        cols[6].write(dataset.get("userCount", 0))
        cols[7].write(dataset.get("alphaCount", 0))
        cols[8].write(dataset.get("fieldCount", 0))
        cols[9].write(dataset.get("pyramidMultiplier", ""))
                
else:
    st.info("当前筛选条件下没有找到数据集")
    st.session_state.current_page = 1

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
    neutralization = st.selectbox(
        "中性化选项",
        ["SIZE", "SECTOR", "VOLATILITY", "LIQUIDITY", "MOMENTUM"]
    )

with col2:
    decay = st.number_input("衰减天数", min_value=1, max_value=30, value=5)

with col3:
    truncation = st.slider("截断百分比", 0.0, 10.0, 5.0, 0.1)

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