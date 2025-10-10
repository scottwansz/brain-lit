import streamlit as st
import sys
import os
import time
import random
import pandas as pd

from brain_lit.svc.check import check_by_query, get_check_and_submit_task_manager

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brain_lit.logger import setup_logger
from brain_lit.sidebar import render_sidebar
from brain_lit.svc.alpha_query import query_submittable_alpha_stats, query_submittable_alpha_details

# 设置logger
logger = setup_logger()

# 渲染共享的侧边栏
render_sidebar()

st.title("📤 提交Alpha")

# 主要内容区域
st.markdown("在本页面您可以提交经过验证的Alpha表达式。")

# Phase输入栏位和统计按钮
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    phase = st.text_input("Phase", value="1")
with col2:
    sharp_threshold = st.number_input("Sharp阈值", value=1.0, min_value=0.0, step=0.1)
with col3:
    fitness_threshold = st.number_input("Fitness阈值", value=0.8, min_value=0.0, step=0.1)
with col4:
    st.write("")  # 空白行用于对齐
    st.write("")
    query_button = st.button("统计可提交的Alpha", type="primary")

# 显示分类统计信息
if query_button:
    # 保存查询状态，确保即使重新渲染页面也能保持显示
    st.session_state.submittable_alpha_stats = True
    st.session_state.phase_value = phase
    st.session_state.sharp_threshold = sharp_threshold
    st.session_state.fitness_threshold = fitness_threshold
    
    # 获取侧边栏条件
    region = st.session_state.get('selected_region', 'CHN')
    universe = st.session_state.get('selected_universe', 'TOP2000U')
    delay = st.session_state.get('selected_delay', 1)
    phase_value = st.session_state.get('phase_value', '1')
    sharp_val = st.session_state.get('sharp_threshold', 1.0)
    fitness_val = st.session_state.get('fitness_threshold', 0.8)
    
    # 查询各分类下的Alpha数量
    category_counts = query_submittable_alpha_stats(region, universe, delay, phase_value, sharp_val, fitness_val)
    
    # 保存分类统计结果到session_state
    st.session_state.category_counts = category_counts

# 如果已经查询过，显示之前的结果
if st.session_state.get('submittable_alpha_stats'):
    # 获取侧边栏条件
    region = st.session_state.get('selected_region', 'CHN')
    universe = st.session_state.get('selected_universe', 'TOP2000U')
    delay = st.session_state.get('selected_delay', 1)
    phase_value = st.session_state.get('phase_value', '1')
    sharp_val = st.session_state.get('sharp_threshold', 1.0)
    fitness_val = st.session_state.get('fitness_threshold', 0.8)
    category_counts = st.session_state.get('category_counts', [])
    
    if category_counts:
        st.subheader("各分类可提交Alpha数量")
        
        # 构建选项列表
        category_options = [f"{row['category']} ({row['count']}个)" for row in category_counts]
        
        # 初始化选中的分类
        if 'selected_category_radio' not in st.session_state:
            st.session_state.selected_category_radio = category_options[0] if category_options else ""
        
        # 使用st.session_state来跟踪当前选中的分类
        if 'current_selected_category' not in st.session_state:
            st.session_state.current_selected_category = st.session_state.selected_category_radio
        
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
                    if st.button(option, key=f"cat_btn_{i}", type=button_type):
                        st.session_state.current_selected_category = option
                        # 更新需要查询详细信息的标志
                        st.session_state.need_detail_query = True
                        # 重新运行以更新按钮状态
                        st.rerun()
        
        # 更新选中的分类
        selected_category = st.session_state.current_selected_category
        
        # 提取选中的分类名
        chosen_category = selected_category.split(" (")[0] if selected_category else None
        
        # 检查是否需要查询详细信息
        need_detail_query = st.session_state.get('need_detail_query', False)
        
        if need_detail_query and chosen_category:
            # 查询选中分类的详细Alpha信息
            alpha_details = query_submittable_alpha_details(region, universe, delay, phase_value, chosen_category, sharp_val, fitness_val)
            
            # 保存当前选中分类的详细信息到session_state
            st.session_state.current_category_details = alpha_details
            st.session_state.current_chosen_category = chosen_category
            # 重置查询标志
            st.session_state.need_detail_query = False
        else:
            # 使用之前缓存的详细信息（如果选中的分类没有改变）
            if st.session_state.get('current_chosen_category') == chosen_category:
                alpha_details = st.session_state.get('current_category_details', [])
            else:
                alpha_details = []
        
        # 显示详细信息表格
        if alpha_details and chosen_category:
            st.subheader(f"{chosen_category}分类下的可提交Alpha")
            df = pd.DataFrame(alpha_details)
            # 移除不需要的列
            columns_to_drop = [col for col in df.columns if col in ['rn', 'simulated', 'passed']]
            df = df.drop(columns=columns_to_drop)
            st.dataframe(df)
            
            # 提供选择功能
            selected_alpha_name = st.selectbox(
                "选择一个Alpha进行提交:",
                [row['name'] for row in alpha_details]
            )
            
            # 显示选中的Alpha表达式
            if selected_alpha_name:
                selected_alpha = next((row for row in alpha_details if row['name'] == selected_alpha_name), None)
                if selected_alpha:
                    st.session_state['pending_alpha'] = selected_alpha['alpha']
                    st.success(f"已选择Alpha: {selected_alpha_name}")
        elif need_detail_query and chosen_category:
            st.info("该分类下暂无可提交的Alpha")
    else:
        st.info("暂无可提交的Alpha")

# 显示Alpha表达式
st.subheader("待提交的Alpha表达式")
pending_alpha = st.session_state.get('pending_alpha', '')
if pending_alpha:
    st.code(pending_alpha, language="python")
else:
    st.info("暂无待提交的Alpha表达式")

# 操作按钮
st.markdown("---")
col3, col4, col5 = st.columns([1, 1, 4])

task_manager = get_check_and_submit_task_manager()

with col3:
    if st.button("提交Alpha", type="primary"):
        # 获取侧边栏条件
        region = st.session_state.get('selected_region', 'CHN')
        universe = st.session_state.get('selected_universe', 'TOP2000U')
        delay = st.session_state.get('selected_delay', 1)
        phase_value = st.session_state.get('phase_value', '1')
        sharp_val = st.session_state.get('sharp_threshold', 1.0)
        fitness_val = st.session_state.get('fitness_threshold', 0.8)

        # 更新选中的分类
        selected_category = st.session_state.current_selected_category

        # 提取选中的分类名
        chosen_category = selected_category.split(" (")[0] if selected_category else None

        query = {
            "region": region,
            "universe": universe,
            "delay": delay,
            "phase": phase_value,
            "category": chosen_category,
        }

        task_manager.start(query=query)

if col4.button("提交状态"):
    # 显示simulate_tasks信息
    st.write("当前提交状态信息:")
    st.json(task_manager.status)

if col5.button("停止提交"):
    task_manager.status["stop"] = True