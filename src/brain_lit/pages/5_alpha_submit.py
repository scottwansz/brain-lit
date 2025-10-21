import os
import sys

import pandas as pd
import streamlit as st

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brain_lit.logger import setup_logger
from brain_lit.sidebar import render_sidebar
from brain_lit.svc.alpha_query import query_submittable_alpha_stats, query_submittable_alpha_details
from brain_lit.svc.submit import get_submit_task_manager

# 设置logger
logger = setup_logger(__name__)

# 渲染共享的侧边栏
render_sidebar()

st.title("📤 提交Alpha")

# 主要内容区域
st.markdown("在本页面您可以提交已通过检查的Alpha。")

# Phase输入栏位和统计按钮
col1, col2 = st.columns([1, 1])
with col1:
    phase = st.number_input("Phase", min_value=1, max_value=9, value=1, step=1)
with col2:
    st.write("")  # 空白行用于对齐
    query_button = st.button("统计可提交的Alpha", type="primary")

# 显示分类统计信息
if query_button:
    # 保存查询状态，确保即使重新渲染页面也能保持显示
    st.session_state.submittable_alpha_stats = True
    st.session_state.phase_value = phase
    
    # 获取侧边栏条件
    region = st.session_state.get('selected_region', 'CHN')
    universe = st.session_state.get('selected_universe', 'TOP2000U')
    delay = st.session_state.get('selected_delay', 1)
    phase_value = st.session_state.get('phase_value', '1')
    
    # 查询各分类下的Alpha数量
    submittable_category_counts = query_submittable_alpha_stats(region, universe, delay, phase_value)
    
    # 保存分类统计结果到session_state
    st.session_state.submittable_category_counts = submittable_category_counts

# 如果已经查询过，显示之前的结果
if st.session_state.get('submittable_alpha_stats'):
    # 获取侧边栏条件
    region = st.session_state.get('selected_region', 'CHN')
    universe = st.session_state.get('selected_universe', 'TOP2000U')
    delay = st.session_state.get('selected_delay', 1)
    phase_value = st.session_state.get('phase_value', '1')
    submittable_category_counts = st.session_state.get('submittable_category_counts', [])
    
    if submittable_category_counts:
        st.subheader("各分类可提交Alpha数量")
        
        # 添加"全选"复选框
        select_all = st.checkbox("全选", key='select_all_categories')
        
        # 构建选项列表
        category_options = [f"{row['category']} ({row['count']}个)" for row in submittable_category_counts]
        
        # 初始化选中的分类
        if 'selected_category_radio' not in st.session_state:
            st.session_state.selected_category_radio = category_options[0] if category_options else ""
        
        # 使用st.session_state来跟踪当前选中的分类
        if 'current_selected_category' not in st.session_state:
            st.session_state.current_selected_category = st.session_state.selected_category_radio
            
        # 如果选择了"全选"，则显示特殊标记
        if select_all:
            st.info("已选择全部分类")
        
        # 创建水平布局的按钮组来模拟radio按钮
        num_categories = len(category_options)
        if num_categories > 0:
            # 计算每行显示的按钮数量
            cols_per_row = min(num_categories, 4)  # 每行最多4个
            cols = st.columns(cols_per_row)
            
            # 显示分类按钮
            for i, option in enumerate(category_options):
                col_idx = i % cols_per_row
                with cols[col_idx]:
                    # 如果这个分类被选中，显示为primary按钮，否则显示为secondary
                    button_type = "primary" if option == st.session_state.current_selected_category else "secondary"
                    if st.button(option, key=f"cat_btn_{i}", type=button_type, disabled=select_all):
                        st.session_state.current_selected_category = option
                        # 重新运行以更新按钮状态
                        st.rerun()
        
        # 更新选中的分类
        selected_category = st.session_state.current_selected_category
        
        # 提取选中的分类名
        chosen_category = selected_category.split(" (")[0] if selected_category else None
        
        # 如果选择了"全选"，则将chosen_category设置为None
        if st.session_state.get('select_all_categories', False):
            chosen_category = None

        # 查询选中分类的详细Alpha信息
        alpha_details = query_submittable_alpha_details(region, universe, delay, phase_value, chosen_category)

        # 保存当前选中分类的详细信息到session_state
        st.session_state.current_category_details = alpha_details
        st.session_state.current_chosen_category = chosen_category
        
        # 显示详细信息表格
        if alpha_details:
            st.subheader(f"{chosen_category}分类下的可提交Alpha")
            df = pd.DataFrame(alpha_details)
            # 移除不需要的列
            columns_to_drop = [col for col in df.columns if col in ['rn', 'simulated', 'passed', 'submitted']]
            df = df.drop(columns=columns_to_drop)
            
            # 保存DataFrame到session_state
            st.session_state.df = df
            
            # 使用st.dataframe显示并启用多行选择
            st.write("请选择要提交的Alpha:")
            selection_event = st.dataframe(
                df,
                key="alpha_selection",
                on_select="rerun",
                selection_mode=["multi-row"],
            )
            
            # 保存选中的行到session_state
            st.session_state.selected_rows = selection_event.selection.rows if selection_event.selection else []
            
            # 显示选中的行数
            if st.session_state.selected_rows:
                st.success(f"已选择 {len(st.session_state.selected_rows)} 个Alpha")
            else:
                st.info("请在上方表格中选择要提交的Alpha")
        else:
            st.info("该分类下暂无可提交的Alpha")
    else:
        st.info("暂无可提交的Alpha")

col3, col4, col5 = st.columns([1, 1, 4])

task_manager = get_submit_task_manager()

with col3:
    if st.button("提交Alpha", type="primary"):
        # 获取选中的数据
        if 'selected_rows' in st.session_state and 'df' in st.session_state:
            selected_df = st.session_state.df.iloc[st.session_state.selected_rows]
            if not selected_df.empty:
                # 转换为记录列表
                records = selected_df.to_dict('records')
                
                # 提交选中的Alpha
                task_manager.start(records=records)
                
                st.success(f"开始提交 {len(records)} 个Alpha")
            else:
                st.warning("请先选择要提交的Alpha")
        else:
            st.warning("请先查询并选择要提交的Alpha")

if col4.button("检查状态"):
    # 显示提交状态信息
    st.write("当前提交状态信息:")
    st.json(task_manager.status)