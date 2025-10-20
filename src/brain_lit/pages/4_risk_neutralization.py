import streamlit as st
import pandas as pd
import sys
import os

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brain_lit.sidebar import render_sidebar
from brain_lit.svc.alpha_query import query_submittable_alpha_details

# 渲染共享的侧边栏
render_sidebar()

st.title("🛡️ Risk Neutralization")

# 从session state获取已选择的参数
selected_region = st.session_state.selected_region
selected_universe = st.session_state.selected_universe
selected_delay = st.session_state.selected_delay
selected_category = st.session_state.selected_category

# 查询条件
st.subheader("查询条件")

col1, col2, col3 = st.columns(3)
with col1:
    sharp_threshold = st.number_input("Sharp阈值", value=1.0, min_value=0.0, step=0.1)
    
with col2:
    fitness_threshold = st.number_input("Fitness阈值", value=0.8, min_value=0.0, step=0.1)
    
with col3:
    phase = st.number_input("Phase", min_value=1, max_value=9, value=1, step=1)

# 查询按钮
if st.button("查询最佳Alphas"):
    with st.spinner("正在查询最佳Alphas..."):
        # 调用查询函数获取最佳Alphas
        best_alphas = query_submittable_alpha_details(
            region=selected_region,
            universe=selected_universe,
            delay=selected_delay,
            phase=phase,
            category=selected_category,
            sharp_threshold=sharp_threshold,
            fitness_threshold=fitness_threshold
        )
        
        if best_alphas:
            st.session_state.best_alphas = best_alphas
            st.success(f"成功查询到 {len(best_alphas)} 个最佳Alphas")
        else:
            st.warning("未找到符合查询条件的最佳Alphas")
            st.session_state.best_alphas = []

# 显示查询结果
if "best_alphas" in st.session_state and st.session_state.best_alphas:
    st.subheader("最佳Alphas列表")
    
    # 转换为DataFrame
    df = pd.DataFrame(st.session_state.best_alphas)
    
    # 选择需要显示的列
    display_columns = ['id', 'name', 'alpha', 'sharp', 'fitness', 'decay', 'neutralization', 'category']
    df_display = df[display_columns].copy()
    
    # 使用st.dataframe显示，启用选择功能
    event = st.dataframe(
        df_display,
        key="alpha_selection",
        on_select="rerun",
        selection_mode="multi-row",
        hide_index=True,
        width='stretch'
    )
    
    # 保存选择的行索引
    st.session_state.selected_rows = event.selection.rows if event and event.selection else []

# Neutralization选择
st.subheader("Neutralization选项")
st.info("请先查询最佳Alphas后再进行以下操作")

# 显示可选择的neutralization列表
neutralization_array = [
    "NONE",
    "REVERSION_AND_MOMENTUM",
    "STATISTICAL",
    "CROWDING",
    "FAST",
    "SLOW",
    "MARKET",
    "SECTOR",
    "INDUSTRY",
    "SUBINDUSTRY",
    "SLOW_AND_FAST",
    "STATISTICAL",
    "COUNTRY"
]
selected_neutralization_opts = st.multiselect(
    "选择Neutralization类型",
    options=neutralization_array,
    default=["SLOW", "FAST", "SLOW_AND_FAST", "CROWDING", "STATISTICAL", "REVERSION_AND_MOMENTUM"]
)

new_phase = st.number_input("新Alpha的Phase", min_value=1, max_value=9, value=2, step=1)

# 生成Risk Neutralization Alphas按钮
if st.button("生成Risk Neutralization Alphas", type="primary"):
    # 检查是否有选中的alphas
    if "best_alphas" not in st.session_state:
        st.warning("请先查询最佳Alphas")
    elif "selected_rows" not in st.session_state or not st.session_state.selected_rows:
        st.warning("请至少选择一个Alpha")
    elif not selected_neutralization_opts:
        st.warning("请至少选择一个Neutralization类型")
    else:
        # 获取选中的alphas
        selected_alphas = [st.session_state.best_alphas[i] for i in st.session_state.selected_rows]
        
        # 生成新的alphas（模拟过程）
        new_alphas = []
        for alpha in selected_alphas:
            for neutralization in selected_neutralization_opts:
                # 从原始alpha中选择一部分属性来创建新的alpha
                new_alpha = {
                    'region': alpha.get('region'),
                    'universe': alpha.get('universe'),
                    'delay': alpha.get('delay'),
                    'alpha': alpha.get('alpha'),
                    'decay': alpha.get('decay'),
                    'name': alpha.get('name'),
                    'category': alpha.get('category'),
                    'dataset': alpha.get('dataset'),
                    'neutralization': neutralization,
                    'phase': new_phase
                }
                new_alphas.append(new_alpha)
        
        # 显示新生成的alphas
        if new_alphas:
            st.subheader("新生成的Risk Neutralization Alphas")
            new_df = pd.DataFrame(new_alphas)
            st.dataframe(new_df, width='stretch')
            st.success(f"成功生成 {len(new_alphas)} 个Risk Neutralization Alphas")
        else:
            st.warning("未能生成新的Risk Neutralization Alphas")
else:
    st.info("选择Alpha和Neutralization类型后，点击'生成Risk Neutralization Alphas'按钮")