import streamlit as st
import pandas as pd
import sys
import os

from svc.logger import setup_logger
from svc.neutralize import neutralization_array, neutralize

logger = setup_logger(__name__)

# 添加src目录到路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sidebar import render_sidebar
from svc.alpha_query import query_checkable_alpha_details
from svc.database import batch_insert_records, update_table

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

with st.container(horizontal=True):
    phase = st.number_input("Phase", min_value=1, max_value=9, value=1, step=1)
    sharp_threshold = st.number_input("Sharp阈值", value=1.0, min_value=0.0, step=0.1)
    fitness_threshold = st.number_input("Fitness阈值", value=0.8, min_value=0.0, step=0.05)

with st.container(horizontal=True, horizontal_alignment="left", vertical_alignment="bottom"):
    passed = st.number_input("Passed状态", min_value=-2, max_value=2, value=0, step=1)

    neutralization = st.selectbox(
        "中性化选项",
        neutralization_array,
        index=0
    )

    # 查询按钮
    if st.button("查询最佳Alphas"):
        st.session_state.new_alphas_to_save = None
        with st.spinner("正在查询最佳Alphas..."):
            # 调用查询函数获取最佳Alphas
            best_alphas = query_checkable_alpha_details(
                region=selected_region,
                universe=selected_universe,
                delay=selected_delay,
                phase=phase,
                category=selected_category if selected_category != "" else None,  # 如果选择"All"则传递None
                sharp_threshold=sharp_threshold,
                fitness_threshold=fitness_threshold,
                passed=passed,
                neutralization=neutralization if neutralization != "NONE" else None
            )

            # 排除best_alphas中used属性为'1'的记录
            best_alphas = [alpha for alpha in best_alphas if alpha.get('used') != 1]

            if best_alphas:
                st.session_state.best_alphas = best_alphas
                st.toast(f":green[成功查询到 {len(best_alphas)} 个最佳Alphas]", icon="✅")
            else:
                st.toast(f":orange[未找到符合查询条件的最佳Alphas]", icon="❌")
                st.session_state.best_alphas = []

# 显示查询结果
if "best_alphas" in st.session_state and st.session_state.best_alphas:
    st.subheader("最佳Alphas列表")
    
    # 转换为DataFrame
    df = pd.DataFrame(st.session_state.best_alphas)
    
    # 选择需要显示的列
    # display_columns = ['id', 'name', 'alpha', 'sharp', 'fitness', 'decay', 'neutralization', 'category']
    df_display = df.copy()  # [display_columns]
    
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

col_new_phase, col_selected_neutralization_opts = st.columns([1, 3])

with col_new_phase:
    new_phase = st.number_input("新Alpha的Phase", min_value=1, max_value=9, value=2, step=1)

# 显示可选择的neutralization列表

with col_selected_neutralization_opts:
    selected_neutralization_opts = st.multiselect(
        "选择Neutralization类型",
        options=neutralization_array,
        default=neutralization_array # ["MARKET", "SECTOR", "INDUSTRY", "COUNTRY"]
    )

# 生成Risk Neutralization Alphas按钮
if st.button("生成Risk Neutralization Alphas"):
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
        st.session_state.new_alphas_to_save = neutralize(selected_alphas, selected_neutralization_opts, new_phase=new_phase)

# 显示新生成的alphas
if st.session_state.get("new_alphas_to_save"):
    new_alphas = st.session_state.new_alphas_to_save
    st.subheader("新生成的Risk Neutralization Alphas")
    new_df = pd.DataFrame(new_alphas)
    st.dataframe(new_df, width='stretch')

    st.success(f"成功生成 {len(new_alphas)} 个Risk Neutralization Alphas")
else:
    st.info("没有新生成的Risk Neutralization Alphas")

# 保存到数据库按钮
if st.button("保存到数据库"):
    st.session_state.save_new_alphas = True

    # 根据地区确定表名，如果region为None则使用all_alphas表
    if selected_region is not None:
        table_name = f"{selected_region.lower()}_alphas"
    else:
        table_name = "all_alphas"

    # 更新原记录使用状态
    selected_alphas = [st.session_state.best_alphas[i] for i in st.session_state.selected_rows]
    old_ids = [alpha.get('id') for alpha in selected_alphas]
    update_table(table_name, {'id': old_ids}, {"used": 1})

    # 处理保存操作
    if st.session_state.save_new_alphas and st.session_state.new_alphas_to_save:
        new_alphas_to_save = st.session_state.new_alphas_to_save
        # 将new_alphas按每200个元素分批处理
        batch_size = 200
        progress_bar = st.progress(0, text="数据保存进度：0.00%")

        try:

            for i in range(0, len(new_alphas_to_save), batch_size):
                batch = new_alphas_to_save[i:i + batch_size]
                affected_rows = batch_insert_records(table_name, batch)

                progress = min((i + batch_size) / len(new_alphas_to_save), 1.0)
                progress_text = f"数据保存进度: {progress:.2%}"
                progress_bar.progress(progress, text=progress_text)

        except Exception as e:
            st.error(f"保存到数据库时发生异常: {str(e)}")
        finally:
            # 清除保存标志
            st.session_state.save_new_alphas = False