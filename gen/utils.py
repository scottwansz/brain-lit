import streamlit as st

from svc.database import insert_record, batch_insert_records


def build_alpha_record(
        region, universe, delay, dataset, name, expression,
        category="sentiment",
        neutralization="SUBINDUSTRY",
        decay=6,
        phase=1,
        template="sentiment_gen"
):
    return {
        "region": region,
        "universe": universe,
        "delay": delay,
        "category": category,
        "dataset": dataset,
        "alpha": expression,
        "name": name,
        "neutralization": neutralization,
        "decay": decay,
        'phase': phase,
        'simulated': 0,
        'used': 0,
        "template": template,
    }


def save_records_to_db(region, universe, delay, dataset, new_alphas, template="sentiment_gen"):
    # 准备dataset_used表中要添加记录
    dataset_used_record = {
        "region": region,
        "universe": universe,
        "delay": delay,
        "dataset": dataset,
        "template": template,
    }

    insert_record("dataset_used", data=dataset_used_record)

    alpha_table_name = f"{region.lower()}_alphas"

    # 将new_alphas按每200个元素分批处理
    batch_size = 200
    progress_bar = st.progress(0, text="数据保存进度：0.00%")
    for i in range(0, len(new_alphas), batch_size):
        batch = new_alphas[i:i + batch_size]
        affected_rows = batch_insert_records(alpha_table_name, batch)

        progress = min((i + batch_size) / len(new_alphas), 1.0)
        progress_text = f"数据保存进度: {progress:.2%}"
        progress_bar.progress(progress, text=progress_text)
