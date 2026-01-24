import streamlit as st
import sys
import os
import time
import random
import pandas as pd

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from svc.logger import setup_logger
from sidebar import render_sidebar
from svc.alpha_query import query_alphas_simulation_stats
from svc.simulate import get_simulate_task_manager

# 设置logger
logger = setup_logger(__name__)

@st.dialog("回测状态")
def show_status():
    st.json(task_manager.simulate_tasks)

st.title("🔬 回测Alpha")

# 渲染共享的侧边栏
render_sidebar()

# 获取SimulateTaskManager实例
task_manager = get_simulate_task_manager()

selected_region = st.session_state.selected_region
selected_universe = st.session_state.selected_universe
selected_delay = st.session_state.selected_delay
selected_category = st.session_state.selected_category

with st.container(horizontal=True, horizontal_alignment="left"):
    phase = st.number_input("Phase", min_value=1, max_value=9, value=1, step=1)
    n_tasks_max = st.number_input("最大任务数", min_value=1, max_value=10, value=8)
    batch_size = st.number_input("批次大小", min_value=1, max_value=10, value=10)

with st.container(horizontal=True, horizontal_alignment="left"):
    if st.button("回测统计", type="primary"):
        # 获取并显示模拟状态统计信息
        simulation_stats = query_alphas_simulation_stats(
            region=selected_region,
            universe=selected_universe,
            delay=selected_delay,
            category=selected_category if selected_category != "" else None,  # 如果选择"All"则传递None
            dataset_ids=None,  # dataset_ids设为None，查询所有数据集
            phase=phase,
        )

        # 显示统计信息
        if simulation_stats:
            # 保存统计信息到session_state，使其在其他操作后仍保持显示
            st.session_state.simulation_stats_data = simulation_stats
        else:
            st.session_state.simulation_stats_data = None

    # 开始回测按钮
    if st.button("开始回测"):
        # 构建查询参数
        query_params = {
            "region": selected_region,
            "universe": selected_universe,
            "delay": selected_delay,
            'simulated': 0,
            'phase': phase
        }

        # 添加分类参数（如果不是"All"）
        if selected_category and selected_category != "All":
            query_params["category"] = selected_category

        # 调用start_simulate方法
        task_manager.start_simulate(query_params, n_tasks_max, batch_size=batch_size)
        st.toast("已开始回测任务")

    # 回测状态按钮
    if st.button("回测状态"):
        show_status()

    # 停止回测按钮
    if st.button("停止回测"):
        # 构建查询参数
        query_params = {
            "region": selected_region,
            "universe": selected_universe,
            "delay": selected_delay,
            "category": selected_category if selected_category != "" else None  # 如果选择"All"则传递None
        }

        # 调用stop_simulate方法
        task_manager.stop_simulate(query_params)
        st.toast("已停止回测任务")

# 显示统计信息（如果存在且未被清除）
if st.session_state.get("simulation_stats_data"):
    # 计算总记录数
    stats = st.session_state.simulation_stats_data
    if stats:
        # 准备用于水平堆叠条形图的数据
        # 转换为DataFrame
        df = pd.DataFrame(stats)
        
        # 将simulated列转换为整数类型
        df['simulated'] = df['simulated'].astype(int)
        
        # 重塑数据以便于绘图
        # 将simulated作为列，category作为行
        pivot_df = df.pivot(index='category', columns='simulated', values='count').fillna(0)
        
        # 确保列的顺序为 0, 1, -1, -2
        desired_order = [0, 1, -1, -2]
        available_columns = [col for col in desired_order if col in pivot_df.columns]
        if available_columns:  # 只有当有可用列时才继续
            pivot_df = pivot_df[available_columns]
            
            # 显示水平堆叠条形图，使用category作为y轴，count作为x轴，simulated作为series
            # 为不同simulated状态手动指定颜色：0使用蓝色，1使用绿色，-1用橙色，-2用红色
            # 直接使用列名作为颜色映射的键
            pivot_df.columns = [str(col) for col in pivot_df.columns]
            colors = ['#3498DB' if col == '0' else '#2ECC71' if col == '1' else '#F39C12' if col == '-1' else '#E74C3C' for col in pivot_df.columns]
            
            st.bar_chart(pivot_df, horizontal=True, color=colors)
        else:
            st.info("暂无有效的统计数据")
    else:
        st.info("暂无统计数据")