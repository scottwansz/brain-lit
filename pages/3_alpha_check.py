import os
import sys

import pandas as pd
import streamlit as st

from svc.check import get_check_task_manager

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from svc.logger import setup_logger
from sidebar import render_sidebar
from svc.alpha_query import query_checkable_alpha_stats, query_checkable_alpha_details

# 设置logger
logger = setup_logger(__name__)

# 渲染共享的侧边栏
render_sidebar()

st.title("✅ 检查Alpha")

# 主要内容区域
st.markdown("在本页面您可以提交Alpha检查任务。")

# Phase输入栏位和统计按钮
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    phase = st.number_input("Phase", min_value=1, max_value=9, value=1, step=1)
with col2:
    sharp_threshold = st.number_input("Sharp阈值", value=1.0, min_value=0.0, step=0.1)
with col3:
    fitness_threshold = st.number_input("Fitness阈值", value=0.8, min_value=0.0, step=0.1)
with col4:
    st.write("")  # 空白行用于对齐
    st.write("")
    query_button = st.button("统计可检查的Alpha", type="primary")

# 显示分类统计信息
if query_button:
    # 保存查询状态，确保即使重新渲染页面也能保持显示
    st.session_state.checkable_alpha_stats = True
    st.session_state.phase_value = phase
    st.session_state.sharp_threshold = sharp_threshold
    st.session_state.fitness_threshold = fitness_threshold
    
    # 获取侧边栏条件
    region = st.session_state.get('selected_region', None)
    universe = st.session_state.get('selected_universe', None)
    delay = st.session_state.get('selected_delay', None)
    phase_value = st.session_state.get('phase_value', '1')
    sharp_val = st.session_state.get('sharp_threshold', 1.0)
    fitness_val = st.session_state.get('fitness_threshold', 0.8)
    
    # 查询各分类下的Alpha数量
    checkable_category_counts = query_checkable_alpha_stats(region, universe, delay, phase_value, sharp_val, fitness_val)
    
    # 保存分类统计结果到session_state
    st.session_state.checkable_category_counts = checkable_category_counts

# 如果已经查询过，显示之前的结果
if st.session_state.get('checkable_alpha_stats'):
    # 获取侧边栏条件
    region = st.session_state.get('selected_region', None)
    universe = st.session_state.get('selected_universe', None)
    delay = st.session_state.get('selected_delay', None)
    phase_value = st.session_state.get('phase_value', '1')
    sharp_val = st.session_state.get('sharp_threshold', 1.0)
    fitness_val = st.session_state.get('fitness_threshold', 0.8)
    checkable_category_counts = st.session_state.get('checkable_category_counts', [])
    
    if checkable_category_counts:
        st.subheader("各分类可检查Alpha数量")
        
        # 添加"全选"复选框
        select_all = st.checkbox("全选", key='select_all_categories')
        
        # 构建选项列表
        category_options = [f"{row['category']} ({row['count']}个)" for row in checkable_category_counts]
        
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
        alpha_details = query_checkable_alpha_details(region, universe, delay, phase_value, chosen_category, sharp_val, fitness_val)

        # 保存当前选中分类的详细信息到session_state
        st.session_state.current_category_details = alpha_details
        st.session_state.current_chosen_category = chosen_category
        
        # 显示详细信息表格
        if alpha_details:
            st.subheader(f"[{chosen_category or '全部'}]分类下的可检查Alpha")
            df = pd.DataFrame(alpha_details)
            # 移除不需要的列
            columns_to_drop = [col for col in df.columns if col in ['rn', 'simulated', 'passed']]
            df = df.drop(columns=columns_to_drop)
            st.dataframe(df)
        else:
            st.info("该分类下暂无可检查的Alpha")

        col3, col4, col5 = st.columns([1, 1, 4])

        task_manager = get_check_task_manager()

        with col3:
            if st.button("检查Alpha", type="primary"):
                alpha_details = st.session_state.current_category_details
                # 组织查询参数字典
                query_params = {
                    'region': region,
                    'universe': universe,
                    'delay': delay,
                    'phase_value': phase_value,
                    'chosen_category': chosen_category,
                    'sharp_val': sharp_val,
                    'fitness_val': fitness_val
                }
                task_manager.start(records=alpha_details, query=query_params)

        if col4.button("检查状态"):
            # 显示simulate_tasks信息
            st.write("当前检查状态信息:")
            st.json(task_manager.status)

        if col5.button("停止检查"):
            task_manager.status["stop"] = True
            task_manager.status["details"] = "Stopped by user"

    else:
        st.info("暂无可检查的Alpha")