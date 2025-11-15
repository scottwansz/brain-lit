import os
import sys
from collections import defaultdict

import streamlit as st

from sidebar import render_sidebar
from svc.database import insert_record, batch_insert_records, query_table
from svc.datafields import get_single_set_fields, get_multi_set_fields
from svc.logger import setup_logger
from svc.neutralize import neutralization_array

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from svc.dataset import get_all_datasets, get_used_dataset_ids
from svc.alpha_query import query_alphas_by_conditions
from svc.alpha_builder import get_alpha_templates, generate_simple_expressions, generate_complex_expressions

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

'''### 选择数据集'''

col_template, unused_col, theme_col, button_col = st.columns([3, 1, 1, 1], vertical_alignment="bottom")

with col_template:
    # 模板选择
    templates = get_alpha_templates()
    template_options = {name: f"{name}: {info['description']}" for name, info in templates.items()}
    selected_template = st.selectbox("选择Alpha模板", options=list(template_options.keys()),
                                    format_func=lambda x: template_options[x])

with unused_col:
    # 获取当前的checkbox状态
    current_show_only_unused = st.checkbox(
        "未使用过",
        value=st.session_state.get("show_only_unused", True),
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
        st.session_state.cached_used_dataset_ids = get_used_dataset_ids(selected_region, selected_universe, selected_delay, selected_template)

# 只有当查询按钮被点击时才继续执行数据集查询和显示逻辑
if st.session_state.get("query_datasets_clicked", False):
    all_datasets = st.session_state.cached_datasets
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
        
        # 准备用于显示的 DataFrame
        import pandas as pd
        
        # 处理数据以便在表格中显示
        display_data = []
        for dataset_dict in filtered_datasets:
            dataset_id = dataset_dict.get("id", "")
            used = dataset_id in used_dataset_ids
            
            # 处理themes字段，显示multiplier值而不是name值
            themes_multiplier = ""
            if isinstance(dataset_dict, dict) and "themes" in dataset_dict:
                themes_multiplier = ", ".join([str(theme.get("multiplier", "")) for theme in dataset_dict.get("themes", [])]) if dataset_dict.get("themes") else ""
            
            display_data.append({
                "ID": f"{dataset_id} 🔵" if used else dataset_id,
                "分类": dataset_dict.get("category", {}).get("name", ""),
                "主题乘数": themes_multiplier,
                "覆盖率": f"{dataset_dict.get('coverage', 0):.2%}",
                "价值评分": dataset_dict.get("valueScore", 0),
                "用户数": dataset_dict.get("userCount", 0),
                "Alpha数": dataset_dict.get("alphaCount", 0),
                "字段数": dataset_dict.get("fieldCount", 0),
                "金字塔乘数": dataset_dict.get("pyramidMultiplier", "")
            })
        
        # 创建 DataFrame
        df = pd.DataFrame(display_data)
        
        # 显示数据集总数
        st.write(f"共找到 {len(filtered_datasets)} 个数据集")
        
        # 使用 st.dataframe 显示数据集，支持行选择
        dataset_selection = st.dataframe(
            df,
            key="dataset_selection",
            on_select="rerun",
            selection_mode="multi-row"
        )
        
        # 处理选中的数据集
        selected_rows = dataset_selection.selection.rows if dataset_selection.selection else []
        st.session_state.selected_datasets = [filtered_datasets[i] for i in selected_rows]
        for row_index in selected_rows:
            dataset_dict = filtered_datasets[row_index]
            dataset_id = dataset_dict.get("id", "")
            st.session_state[f"selected_dataset_{dataset_id}"] = dataset_dict
            
        # 移除未选中的数据集
        selected_dataset_keys = [f"selected_dataset_{filtered_datasets[i].get('id', '')}" for i in selected_rows]
        for key in list(st.session_state.keys()):
            if key.startswith("selected_dataset_") and key not in selected_dataset_keys:
                del st.session_state[key]
                    
    else:
        st.info("当前筛选条件下没有找到数据集")

# 参数设置
st.subheader("参数设置")
col_phase, col1, col2, col3 = st.columns(4)

with col1:
    neutralization = st.selectbox(
        "中性化选项",
        neutralization_array,
        index=9
    )

with col2:
    decay = st.number_input("衰减天数", min_value=1, max_value=30, value=6)

with col3:
    truncation = st.slider("截断百分比", 0.01, 0.1, 0.08, 0.01)

with col_phase:
    phase = st.number_input("新Alpha的Phase", min_value=1, max_value=9, value=1, step=1)

# 操作按钮
st.markdown("---")
col_gen_alphas, col_save_alphas, col_query_alphas, col_clear = st.columns([1, 1, 1, 3])

if col_gen_alphas.button("生成Alpha", type="primary"):        # 获取当前选中的数据集
    if "selected_datasets" in st.session_state and selected_template:

        all_expressions = {}
        alpha_records = []
        for dataset in st.session_state.selected_datasets:

            query_params = {
                "region": selected_region,
                "universe": selected_universe,
                "delay": selected_delay,
                "dataset": dataset.get("id"),
            }

            if templates[selected_template]["category"] == "simple":
                dataset_fields = get_single_set_fields(** query_params)
                dataset_expressions = generate_simple_expressions(dataset_fields, template_name=selected_template)
            else:
                table_name = f"{selected_region.lower()}_alphas"
                best_records = query_table(table_name, query_params)

                simple_expressions = defaultdict(list)
                for record in best_records:
                    simple_expressions[record.get("name")].append(record.get("alpha"))
                dataset_expressions = generate_complex_expressions(simple_expressions, template_name=selected_template)

            # 将dataset_expressions整理成alpha表批量新增记录
            for name in dataset_expressions:
                expressions = dataset_expressions[name]
                for expression in expressions:
                    alpha_record = {
                        "region": selected_region,
                        "universe": selected_universe,
                        "delay": selected_delay,
                        "category": dataset.get("category", {}).get("id"),
                        "dataset": dataset.get("id"),
                        "alpha": expression,
                        "name": name,
                        "neutralization": neutralization,
                        "decay": decay,
                        'phase': phase,
                        'simulated': 0,
                        'used': 0,
                        "template": selected_template,
                    }
                    alpha_records.append(alpha_record)

        st.success(f"使用{selected_template}模板生成了{len(alpha_records)}条Alpha表达式")
        df = pd.DataFrame(alpha_records[:2000])
        st.dataframe(df, width='stretch')
        st.session_state.new_alphas_to_save = alpha_records

    else:
        st.warning("请选择数据集与表达式模板")

if col_save_alphas.button("保存Alpha"):

    if "new_alphas_to_save" in st.session_state:

        if "selected_datasets" in st.session_state and selected_template:

            for dataset in st.session_state.selected_datasets:
                # 准备dataset_used表中要添加记录
                dataset_used_record = {
                    "region": selected_region,
                    "universe": selected_universe,
                    "delay": selected_delay,
                    "dataset": dataset.get("id"),
                    "template": selected_template,
                }

                insert_record("dataset_used", data=dataset_used_record)

        alpha_table_name = f"{selected_region.lower()}_alphas"

        # 将new_alphas按每200个元素分批处理
        batch_size = 200
        new_alphas = st.session_state.new_alphas_to_save
        progress_bar = st.progress(0, text="数据保存进度：0.00%")
        for i in range(0, len(new_alphas), batch_size):
            batch = new_alphas[i:i + batch_size]
            affected_rows = batch_insert_records(alpha_table_name, batch)

            progress = min((i + batch_size) / len(new_alphas), 1.0)
            progress_text = f"数据保存进度: {progress:.2%}"
            progress_bar.progress(progress, text=progress_text)
    else:
        st.warning("请先生成Alpha")

if col_query_alphas.button("查询Alpha"):
    query = {
        "region": selected_region,
        "universe": selected_universe,
        "delay": selected_delay,
        "template": selected_template,
        "phase": phase,
    }

    # 获取当前选中的数据集
    if "selected_datasets" in st.session_state:
        selected_datasets = st.session_state.get("selected_datasets", [])
        selected_dataset_ids = [dataset.get("id", "") for dataset in selected_datasets]
        query["dataset"] = selected_dataset_ids

    if selected_category:
        query["category"] = selected_category

    table_name = f"{selected_region.lower()}_alphas"
    query_results = query_table(table_name, conditions= query)

    if query_results:
        st.session_state.query_results = query_results
        st.session_state.show_query_results = True
        st.rerun()
    else:
        st.info("未找到相关的Alpha记录")
        st.session_state.query_results = None
        st.session_state.show_query_results = False


with col_clear:
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
        df = pd.DataFrame(query_results[:2000])
        st.dataframe(df, width='stretch')
    else:
        st.info("未找到相关记录")