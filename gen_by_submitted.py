import streamlit as st

from gen.utils import build_alpha_record
from svc.alpha_builder import process_field_by_coverage
from svc.auth import get_auto_login_session
from svc.database import batch_insert_records

submitted_region = 'IND'
category='model'
dataset = 'model26'

submitted_fields = [
    'price_to_mean_estimate_ratio_12m_ebitda',
    'price_to_smartest_forward_ebitda_ratio',
    'price_to_mean_estimate_ratio_year2_ebitda',
]

submitted_template = '-ts_av_diff({field}, 5)'

url = "https://api.worldquantbrain.com/data-fields/{field}"
session = get_auto_login_session()

all_records = []

for field in submitted_fields:
    response = session.get(url.format(field=field))
    if response.status_code != 200:
        print(f"获取字段{field}失败")
        print(response.text,  response.status_code)
        # raise Exception(f"获取字段{field}失败")
    field_info = response.json()
    # print(json.dumps( field_info, indent=4,  ensure_ascii=False))

    for rdu in  field_info['data']:
        region = rdu['region']
        delay = rdu['delay']
        universe = rdu['universe']

        if region == submitted_region:
            continue

        processed_field = process_field_by_coverage( field, {'type': field_info['type'],  'coverage': rdu['coverage']})
        expression = submitted_template.format(field=processed_field)
        r = build_alpha_record(region, universe, delay, dataset, field, expression, category=category, template=dataset, phase=9)
        all_records.append(r)

        # alpha_table_name = f"{region.lower()}_alphas"
        # insert_record(alpha_table_name, data=r)

st.dataframe(all_records)
print(len(all_records),  "records generated.")

if st.button("保存到数据库"):
    alpha_table_name = "all_alphas"
    batch_insert_records(alpha_table_name, all_records)