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
    "COUNTRY",
    "SLOW_AND_FAST",
]

def neutralize(selected_alphas, selected_neutralization_opts, new_phase=2):

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
                'used': 1,
                'template': alpha.get('template'),
            }
            new_alphas.append(new_alpha)

    return new_alphas
