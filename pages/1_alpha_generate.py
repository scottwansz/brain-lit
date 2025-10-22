import os
import sys

import streamlit as st

from sidebar import render_sidebar
from svc.datafields import get_all_data_fields
from svc.logger import setup_logger

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from svc.dataset import get_all_datasets, get_used_dataset_ids
from svc.alpha_query import query_alphas_by_conditions
from svc.alpha_builder import get_alpha_templates, AlphaGenerator

# 设置logger
logger = setup_logger(__name__)

# 渲染共享的侧边栏
render_sidebar()

def get_selected_dataset_ids():
    """获取当前选中的数据集列表"""
    selected_datasets = []
    for key in st.session_state:
        if key.startswith("selected_dataset_"):
            dataset_info = st.session_state[key]
            if isinstance(dataset_info, dict):
                dataset_id = dataset_info.get("id", "")
            else:
                dataset_id = dataset_info
            selected_datasets.append(dataset_id)
    return selected_datasets

st.title("📈 生成Alpha")

# 主要内容区域
# st.markdown("在本页面您可以生成新的Alpha表达式。")

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

# 初始化"主题乘数非空"筛选状态
if "filter_non_empty_themes" not in st.session_state:
    st.session_state.filter_non_empty_themes = False

if "filter_non_empty_themes_prev" not in st.session_state:
    st.session_state.filter_non_empty_themes_prev = False

# 从session state获取已选择的参数
selected_region = st.session_state.selected_region
selected_universe = st.session_state.selected_universe
selected_delay = st.session_state.selected_delay
selected_category = st.session_state.selected_category

# 数据集选择部分
# 创建一行来放置标题和控件
title_col, unused_col, theme_col, button_col = st.columns([4, 1, 1, 1])

with title_col:
    st.subheader("数据集选择")

with unused_col:
    # 获取当前的checkbox状态
    current_show_only_unused = st.checkbox(
        "未使用过",
        value=st.session_state.get("show_only_unused", False),
        key="show_only_unused_checkbox"
    )
    # 更新session state
    st.session_state.show_only_unused = current_show_only_unused
    # 当筛选状态改变时重置页码
    if current_show_only_unused != st.session_state.get("show_only_unused_prev", False):
        st.session_state.current_page = 1
        st.session_state.show_only_unused_prev = current_show_only_unused
        if st.session_state.get("query_datasets_clicked", False):
            st.rerun()

with theme_col:
    # 添加"主题乘数非空"过滤选项
    current_filter_non_empty_themes = st.checkbox(
        "主题非空",
        value=st.session_state.get("filter_non_empty_themes", False),
        key="filter_non_empty_themes_checkbox"
    )
    # 更新session state
    st.session_state.filter_non_empty_themes = current_filter_non_empty_themes
    # 当筛选状态改变时重置页码
    if current_filter_non_empty_themes != st.session_state.get("filter_non_empty_themes_prev", False):
        st.session_state.current_page = 1
        st.session_state.filter_non_empty_themes_prev = current_filter_non_empty_themes
        if st.session_state.get("query_datasets_clicked", False):
            st.rerun()

if button_col.button("查询数据集"):
    st.session_state.query_datasets_clicked = True
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
    # session = st.session_state.global_session

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

    # 获取数据集列表
    with st.spinner("正在获取数据集列表..."):
        st.session_state.cached_datasets = get_all_datasets(dataset_params)
        # 获取已使用的数据集列表（一次性获取，避免重复查询数据库）
        st.session_state.cached_used_dataset_ids = get_used_dataset_ids(selected_region, selected_universe, selected_delay)

# 只有当查询按钮被点击时才继续执行数据集查询和显示逻辑
if st.session_state.get("query_datasets_clicked", False):
    all_datasets = st.session_state.cached_datasets
    total_count = len(all_datasets)
    used_dataset_ids = st.session_state.cached_used_dataset_ids

    # 显示数据集选择
    if all_datasets:
        
        # 过滤已使用的数据集（如果用户选择了只显示未使用的数据集）
        show_only_unused = st.session_state.get("show_only_unused", False)
        filter_non_empty_themes = st.session_state.get("filter_non_empty_themes", False)
        
        # 应用筛选条件
        filtered_datasets = all_datasets
        
        # 过滤已使用的数据集
        if show_only_unused:
            filtered_datasets = [
                dataset for dataset in filtered_datasets 
                if not (
                    dataset.get("id", "") if isinstance(dataset, dict) else dataset
                ) in used_dataset_ids
            ]
        
        # 过滤主题乘数非空的数据集
        if filter_non_empty_themes:
            filtered_datasets = [
                dataset for dataset in filtered_datasets
                if isinstance(dataset, dict) and "themes" in dataset and dataset["themes"] and 
                   any(theme.get("multiplier") is not None for theme in dataset["themes"])
            ]
        
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
        count_col, prev_col, info_col, next_col = st.columns([4, 1, 1, 1])
        with count_col:
            if show_only_unused:
                st.write(f"共找到 {filtered_count} 个未使用数据集（总计 {total_count} 个）")
            else:
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
        
        # 计算当前页应该显示的数据
        start_idx = (st.session_state.current_page - 1) * page_size
        end_idx = min(start_idx + page_size, len(filtered_datasets))
        page_datasets = filtered_datasets[start_idx:end_idx]
        # logger.info("page_datasets: %s", page_datasets)
        
        # 显示数据行
        for dataset_dict in page_datasets:
            dataset_id = dataset_dict.get("id", "")
                
            # 检查数据集是否已被使用
            used = dataset_id in used_dataset_ids
            
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
            
            cols[2].write(dataset_dict.get("category", {}).get("name", ""))
            cols[3].write(themes_multiplier)
            cols[4].write(f"{dataset_dict.get("coverage", 0):.2%}")
            cols[5].write(dataset_dict.get("valueScore", 0))
            cols[6].write(dataset_dict.get("userCount", 0))
            cols[7].write(dataset_dict.get("alphaCount", 0))
            cols[8].write(dataset_dict.get("fieldCount", 0))
            cols[9].write(dataset_dict.get("pyramidMultiplier", ""))
                    
    else:
        st.info("当前筛选条件下没有找到数据集")
        st.session_state.current_page = 1

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

col_template = st.columns([1])[0]

with col_template:
    # 模板选择
    templates = get_alpha_templates()
    template_options = {name: f"{name}: {info['description']}" for name, info in templates.items()}
    selected_template = st.selectbox("选择Alpha模板", options=list(template_options.keys()),
                                    format_func=lambda x: template_options[x])

# 操作按钮
st.markdown("---")
col6, col7, col8 = st.columns([1, 1, 3])

if col6.button("生成Alpha", type="primary"):        # 获取当前选中的数据集
    selected_dataset_ids = get_selected_dataset_ids()

    if selected_dataset_ids and selected_template:
        st.success(f"使用{selected_template}模板生成Alpha表达式")
        query_params = {
            "region": selected_region,
            "universe": selected_universe,
            "delay": selected_delay,
            # "category": selected_category,
            "dataset_id": selected_dataset_ids[0],
            # "neutralization": neutralization,
            # "decay": decay,
            # "truncation": truncation
        }
        dataset_fields = get_all_data_fields(** query_params)
        generator = AlphaGenerator(dataset_fields)
        alpha_expression = generator.generate_by_template(selected_template)
        st.json(query_params)
        st.json(alpha_expression)

    else:
        st.warning("请选择数据集与表达式模板")

with col7:
    if st.button("查询Alpha"):
        # 获取当前选中的数据集
        selected_dataset_ids = get_selected_dataset_ids()
        
        # 查询Alpha记录
        query_results = query_alphas_by_conditions(
            selected_region,
            selected_universe,
            selected_delay,
            selected_category,
            selected_dataset_ids  # 传入选中的数据集ID列表
        )
        
        if query_results:
            st.session_state.query_results = query_results
            st.session_state.show_query_results = True
            st.rerun()
        else:
            st.info("未找到相关的Alpha记录")

with col8:
    if st.button("清空"):
        st.rerun()

# 显示查询结果
if st.session_state.get("show_query_results", False):
    st.subheader("查询结果")
    query_results = st.session_state.get("query_results", [])

    if query_results:
        # 显示记录总数
        st.write(f"共找到 {len(query_results)} 条记录")

        # 使用pandas展示结果
        import pandas as pd

        # 创建DataFrame并显示
        df = pd.DataFrame(query_results)
        st.dataframe(df, width='stretch')
    else:
        st.info("未找到相关记录")