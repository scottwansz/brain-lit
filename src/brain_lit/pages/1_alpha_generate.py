import os
import sys

import streamlit as st

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brain_lit.logger import setup_logger
from brain_lit.sidebar import render_sidebar
from brain_lit.svc.dataset import get_all_datasets
from brain_lit.svc.database import get_used_datasets

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

# 初始化缓存
if "cached_datasets" not in st.session_state:
    st.session_state.cached_datasets = {}

# 初始化筛选状态
if "show_only_unused" not in st.session_state:
    st.session_state.show_only_unused = False

if "show_only_unused_prev" not in st.session_state:
    st.session_state.show_only_unused_prev = False

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
    # 参数变化时清除缓存
    cache_keys_to_remove = [key for key in st.session_state.cached_datasets.keys() 
                           if key.startswith(f"{selected_region}_{selected_universe}_{selected_delay}")]
    for key in cache_keys_to_remove:
        del st.session_state.cached_datasets[key]

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
}

# 添加分类参数（如果不是"All"）
if selected_category and selected_category != "All":
    dataset_params["category"] = selected_category

# 生成缓存键
cache_key = f"{selected_region}_{selected_universe}_{selected_delay}_{selected_category}_all"

# 获取数据集列表
with st.spinner("正在获取数据集列表..."):
    # 检查是否有缓存的数据
    if cache_key in st.session_state.cached_datasets:
        all_datasets, total_count = st.session_state.cached_datasets[cache_key]
    else:
        # 获取所有数据集
        all_datasets, total_count = get_all_datasets(session, dataset_params)
        # 缓存数据
        st.session_state.cached_datasets[cache_key] = (all_datasets, total_count)

datasets = all_datasets

# 显示数据集选择
if datasets:
    # 获取已使用的数据集列表（一次性获取，避免重复查询数据库）
    used_datasets = get_used_datasets(selected_region, selected_universe, selected_delay)
    
    # 过滤已使用的数据集（如果用户选择了只显示未使用的数据集）
    show_only_unused = st.session_state.get("show_only_unused", False)
    if show_only_unused:
        filtered_datasets = [
            dataset for dataset in datasets 
            if not (
                dataset.get("id", "") if isinstance(dataset, dict) else dataset
            ) in used_datasets
        ]
    else:
        filtered_datasets = datasets
    
    # 计算过滤后的数据集数量
    filtered_count = len(filtered_datasets)
    
    # 计算总页数
    page_size = 20  # 每页显示的数据条数
    if show_only_unused:
        total_pages = (filtered_count + page_size - 1) // page_size if filtered_count > 0 else 1
        display_count = filtered_count
    else:
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        display_count = total_count
    
    # 确保当前页码在有效范围内
    if st.session_state.current_page > total_pages:
        st.session_state.current_page = total_pages
    if st.session_state.current_page < 1:
        st.session_state.current_page = 1
    
    # 在同一行显示数据集总数、筛选选项和分页控件
    count_col, filter_col, _, prev_col, info_col, next_col = st.columns([3, 2, 1, 1, 2, 1])
    with count_col:
        if show_only_unused:
            st.write(f"共找到 {filtered_count} 个未使用数据集（总计 {total_count} 个）")
        else:
            st.write(f"共找到 {total_count} 个数据集")
    with filter_col:
        # 获取当前的checkbox状态
        current_show_only_unused = st.checkbox(
            "只显示未使用过的数据集", 
            value=st.session_state.get("show_only_unused", False),
            key="show_only_unused_checkbox"
        )
        # 更新session state
        st.session_state.show_only_unused = current_show_only_unused
        # 当筛选状态改变时重置页码
        if current_show_only_unused != st.session_state.get("show_only_unused_prev", False):
            st.session_state.current_page = 1
            st.session_state.show_only_unused_prev = current_show_only_unused
            st.rerun()
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
    
    # 计算当前页应该显示的数据
    start_idx = (st.session_state.current_page - 1) * page_size
    end_idx = min(start_idx + page_size, len(filtered_datasets))
    page_datasets = filtered_datasets[start_idx:end_idx]
    
    # 显示数据行
    for dataset in page_datasets:
        # 确保dataset是字典类型
        if isinstance(dataset, str):
            dataset_id = dataset
            dataset_dict = {"id": dataset_id}
        else:
            dataset_dict = dataset
            dataset_id = dataset_dict.get("id", "")
            
        # 检查数据集是否已被使用
        used = dataset_id in used_datasets
        
        # 处理themes字段，显示multiplier值而不是name值
        themes_multiplier = ""
        if isinstance(dataset_dict, dict) and "themes" in dataset_dict:
            themes_multiplier = ", ".join([str(theme.get("multiplier", "")) for theme in dataset_dict.get("themes", [])]) if dataset_dict.get("themes") else ""
        
        # 创建数据行
        cols = st.columns([1, 2, 2, 1, 1, 1, 1, 1, 1, 1])
        
        # 复选框
        with cols[0]:
            is_selected = st.checkbox(
                f"选择数据集 {dataset_id}", 
                key=f"select_{dataset_id}",
                value=st.session_state.get(f"selected_dataset_{dataset_id}", False),
                label_visibility="collapsed"
            )
            # 更新session state
            if is_selected:
                st.session_state[f"selected_dataset_{dataset_id}"] = dataset_dict
            elif f"selected_dataset_{dataset_id}" in st.session_state:
                del st.session_state[f"selected_dataset_{dataset_id}"]
        
        # 数据集ID列 - 对已使用的数据集使用特殊标记
        with cols[1]:
            if used:
                # 使用特殊颜色和标记来标识已使用的数据集
                st.markdown(f"<span style='color: #1f77b4; font-weight: bold;'>{dataset_id} 🔵</span>", unsafe_allow_html=True)
            else:
                st.write(dataset_id)
        
        # 其他数据列
        category_name = ""
        if isinstance(dataset_dict, dict) and "category" in dataset_dict:
            category_data = dataset_dict.get("category", {})
            if isinstance(category_data, dict):
                category_name = category_data.get("name", "")
            else:
                category_name = str(category_data)
        
        coverage = 0.0
        if isinstance(dataset_dict, dict):
            coverage = dataset_dict.get("coverage", 0.0)
            
        value_score = 0
        if isinstance(dataset_dict, dict):
            value_score = dataset_dict.get("valueScore", 0)
            
        user_count = 0
        if isinstance(dataset_dict, dict):
            user_count = dataset_dict.get("userCount", 0)
            
        alpha_count = 0
        if isinstance(dataset_dict, dict):
            alpha_count = dataset_dict.get("alphaCount", 0)
            
        field_count = 0
        if isinstance(dataset_dict, dict):
            field_count = dataset_dict.get("fieldCount", 0)
            
        pyramid_multiplier = ""
        if isinstance(dataset_dict, dict):
            pyramid_multiplier = dataset_dict.get("pyramidMultiplier", "")
        
        cols[2].write(category_name)
        cols[3].write(themes_multiplier)
        cols[4].write(f"{coverage:.2%}")
        cols[5].write(value_score)
        cols[6].write(user_count)
        cols[7].write(alpha_count)
        cols[8].write(field_count)
        cols[9].write(pyramid_multiplier)
                
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