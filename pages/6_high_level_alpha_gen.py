import streamlit as st

from gen.phase2_gen import get_phase1_alphas, get_group_second_order_factory
from sidebar import render_sidebar
from svc.database import batch_insert_records, update_table
from svc.logger import setup_logger

logger = setup_logger(__name__)

# 渲染共享的侧边栏
render_sidebar()

st.title("High Level Alpha Gen")

region = st.session_state.get('selected_region', 'all') or 'all'
delay = st.session_state.get('selected_delay', 1) or 1

with st.container(horizontal= True, horizontal_alignment="left", vertical_alignment="bottom"):
    target_level = st.radio("Target Level:", ("2", "3"), horizontal= True)

    if st.button("Query"):

        if target_level == "2":
            st.session_state.phase_n_records = get_phase1_alphas(region, delay=0)
        else:
            phase_n_records = []

select_rows = []
if 'phase_n_records' in st.session_state:
    st.info(f"查询到以下 {len(st.session_state.phase_n_records)} 个Alpha：")
    select_event = st.dataframe(st.session_state.phase_n_records, selection_mode="multi-row", on_select="rerun")
    selected_rows_idx = select_event.selection.rows if select_event and select_event.selection else []
    select_rows = [st.session_state.phase_n_records[i] for i in selected_rows_idx]

with st.container(horizontal= True, horizontal_alignment="left", vertical_alignment="bottom"):
    phase = st.number_input("Phase:", min_value=1, max_value=9, value=9, step=1, key="phase")

    if st.button("Gen", disabled=not select_rows):
        new_records = []
        group_ops = ["group_neutralize", "group_rank", "group_zscore"]

        for r in select_rows:
            expr = r['alpha']
            for alpha in get_group_second_order_factory([expr], group_ops, region):
                new_record = r.copy()
                new_record['alpha'] = alpha
                new_record['phase'] = phase
                new_record['template'] = f'phase{target_level}'
                new_record['simulated'] = 0
                new_record['used'] = int(target_level)
                new_record.pop('id')
                new_record.pop('rn')
                new_records.append(new_record)

        st.session_state.alphas_to_save = new_records

    if st.button("Save", disabled=not 'alphas_to_save' in st.session_state):
        st.session_state.save_new_alphas = True

if 'alphas_to_save' in st.session_state and 'save_new_alphas' in st.session_state and st.session_state.save_new_alphas:
    # 将new_alphas按每200个元素分批处理
    batch_size = 200
    new_alphas = st.session_state.alphas_to_save
    table_name = f"{region.lower()}_alphas"
    progress_bar = st.progress(0, text="数据保存进度：0.00%")

    for i in range(0, len(new_alphas), batch_size):
        batch = new_alphas[i:i + batch_size]
        affected_rows = batch_insert_records(table_name, batch)

        progress = min((i + batch_size) / len(new_alphas), 1.0)
        progress_text = f"数据保存进度: {progress:.2%}"
        progress_bar.progress(progress, text=progress_text)

    old_ids = [alpha.get('id') for alpha in select_rows]
    update_table(table_name, {'id': old_ids}, {"used": int(target_level)})

    st.success(f"成功保存 {len(st.session_state.alphas_to_save)} 个Alpha")
    st.session_state.save_new_alphas = False

if 'alphas_to_save' in st.session_state:
    st.info(f"以下 {len(st.session_state.alphas_to_save)} 个Alpha将保存：")
    st.dataframe(st.session_state.alphas_to_save)