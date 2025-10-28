from svc.database import update_table

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

def neutralize(selected_alphas, selected_neutralization_opts, new_phase=2):

    # 更新原记录使用状态
    table_name = f"{selected_alphas[0]['region'].lower()}_alphas"
    old_ids = [alpha.get('id') for alpha in selected_alphas]
    update_table(table_name, {'id': old_ids}, {"used": 1})

    new_alphas = []

    for alpha in selected_alphas:
        for neutralization in selected_neutralization_opts:
            # 从原始alpha中选择一部分属性来创建新的alpha
            new_alpha = {
                'region': alpha.get('region'),
                'universe': alpha.get('universe'),
                'delay': alpha.get('delay'),
                'alpha': alpha.get('alpha'),
                'name': alpha.get('name'),
                'category': alpha.get('category'),
                'dataset': alpha.get('dataset'),
                'neutralization': neutralization,
                'decay': alpha.get('decay'),
                'phase': new_phase,
                'simulated': 0,
                'used': 1
            }
            new_alphas.append(new_alpha)

    return new_alphas
