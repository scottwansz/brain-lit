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

# Alpha表达式输入区域
st.subheader("Alpha表达式")
alpha_expression = st.text_area(
    "请输入您的Alpha表达式:",
    height=200,
    placeholder="# 示例Alpha表达式\n# rank(correlation(close, returns, 5))"
)

# 定义地区、延迟和股票池的映射关系
REGION_PARAMS = {
    "USA": {
        "delay": [1, 0],
        "universe": ["TOP3000", "TOP1000", "TOP500", "TOP200", "ILLIQUID_MINVOL1M", "TPSP500"]
    },
    "GLB": {
        "delay": [1],
        "universe": ["TOP3000", "MINVOL1M"]
    },
    "EUR": {
        "delay": [1, 0],
        "universe": ["TOP2500","TOP1200", "TOP800", "TOP400", "ILLIQUID_MINVOL1M"]
    },
    "ASI": {
        "delay": [1],
        "universe": ["MINVOL1M", "ILLIDQUID_MINVOL1M"]
    },
    "CHN": {
        "delay": [1, 0],
        "universe": ["TOP2000U"]
    }
}

# 定义可用的分类列表
CATEGORIES = [
    ('All', ''),
    ('Analyst', 'analyst'),
    ('Earnings', 'earnings'),
    ('Fundamental', 'fundamental'),
    ('Imbalance', 'imbalance'),
    ('Insiders', 'insiders'),
    ('Institutions', 'institutions'),
    ('Macro', 'macro'),
    ('Model', 'model'),
    ('News', 'news'),
    ('Option', 'option'),
    ('Other', 'other'),
    ('Price Volume', 'pv'),
    ('Risk', 'risk'),
    ('Sentiment', 'sentiment'),
    ('Short Interest', 'shortinterest'),
    ('Social Media', 'socialmedia')
]

# 初始化session state中的参数
if "selected_region" not in st.session_state:
    st.session_state.selected_region = "USA"
if "selected_universe" not in st.session_state:
    st.session_state.selected_universe = REGION_PARAMS["USA"]["universe"][0]
if "selected_delay" not in st.session_state:
    st.session_state.selected_delay = REGION_PARAMS["USA"]["delay"][0]
if "selected_category" not in st.session_state:
    st.session_state.selected_category = ""
if "current_page" not in st.session_state:
    st.session_state.current_page = 1

# 参数设置
st.subheader("参数设置")
col1, col2, col3, col4 = st.columns(4)

with col1:
    start_date = st.date_input("开始日期", value=None)
    selected_region = st.selectbox("地区", list(REGION_PARAMS.keys()), 
                                   index=list(REGION_PARAMS.keys()).index(st.session_state.selected_region),
                                   key="region_select")
    # 更新session state
    st.session_state.selected_region = selected_region

with col2:
    end_date = st.date_input("结束日期", value=None)
    # 根据选择的地区动态更新股票池选项
    universe_options = REGION_PARAMS[selected_region]["universe"]
    # 确保默认值在选项列表中
    default_universe_index = 0
    if st.session_state.selected_universe in universe_options:
        default_universe_index = universe_options.index(st.session_state.selected_universe)
    selected_universe = st.selectbox("股票池", universe_options,
                                     index=default_universe_index,
                                     key="universe_select")
    # 更新session state
    st.session_state.selected_universe = selected_universe

with col3:
    decay = st.number_input("衰减天数", min_value=1, max_value=30, value=5)
    # 根据选择的地区动态更新延迟天数选项
    delay_options = REGION_PARAMS[selected_region]["delay"]
    # 确保默认值在选项列表中
    default_delay_index = 0
    if st.session_state.selected_delay in delay_options:
        default_delay_index = delay_options.index(st.session_state.selected_delay)
    selected_delay = st.selectbox("延迟天数", delay_options,
                                  index=default_delay_index,
                                  key="delay_select")
    # 更新session state
    st.session_state.selected_delay = selected_delay

with col4:
    # 分类选择
    category_options = [cat[0] for cat in CATEGORIES]
    category_values = [cat[1] for cat in CATEGORIES]
    current_category_index = category_values.index(st.session_state.selected_category) if st.session_state.selected_category in category_values else 0
    selected_category_name = st.selectbox("分类", category_options, index=current_category_index)
    selected_category = CATEGORIES[category_options.index(selected_category_name)][1]
    st.session_state.selected_category = selected_category

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
    st.write(f"共找到 {total_count} 个数据集")
    
    # 计算总页数
    page_size = 10
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
    
    # 确保当前页码在有效范围内
    if st.session_state.current_page > total_pages:
        st.session_state.current_page = total_pages
    if st.session_state.current_page < 1:
        st.session_state.current_page = 1
    
    # 显示表格形式的数据集
    # 创建表格标题行
    header_cols = st.columns([1, 2, 2, 1, 1, 1, 1, 1, 1, 2])
    headers = ["选择", "ID", "分类", "覆盖率", "价值评分", "用户数", "Alpha数", "字段数", "金字塔乘数", "主题"]
    
    for col, header in zip(header_cols, headers):
        col.write(f"**{header}**")
    
    # 显示数据行
    for dataset in datasets:
        # 处理themes字段，将其转换为字符串
        themes_str = ", ".join([theme.get("name", "") for theme in dataset.get("themes", [])]) if dataset.get("themes") else ""
        
        # 创建数据行
        cols = st.columns([1, 2, 2, 1, 1, 1, 1, 1, 1, 2])
        
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
        cols[2].write(f"{dataset.get('category', {}).get('name', '')} > {dataset.get('subcategory', {}).get('name', '')}")
        cols[3].write(f"{dataset.get('coverage', 0):.2%}")
        cols[4].write(dataset.get("valueScore", 0))
        cols[5].write(dataset.get("userCount", 0))
        cols[6].write(dataset.get("alphaCount", 0))
        cols[7].write(dataset.get("fieldCount", 0))
        cols[8].write(dataset.get("pyramidMultiplier", 0))
        cols[9].write(themes_str)
                
    # 分页控件
    col_prev, col_page_info, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("上一页", disabled=(st.session_state.current_page <= 1)):
            st.session_state.current_page -= 1
            st.rerun()
            
    with col_page_info:
        st.write(f"第 {st.session_state.current_page} 页，共 {total_pages} 页")
        
    with col_next:
        if st.button("下一页", disabled=(st.session_state.current_page >= total_pages)):
            st.session_state.current_page += 1
            st.rerun()
else:
    st.info("当前筛选条件下没有找到数据集")
    st.session_state.current_page = 1

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