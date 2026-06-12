import itertools

param_grid = {
    'lookback': [5, 10, 21, 63],
    'win_lo': [0.01, 0.05],
    'win_hi': [0.95, 0.99],
}

print(*param_grid.values())

keys = list(param_grid.keys())
combos = list(itertools.product(*param_grid.values()))
print(len(combos))

for i, combo in enumerate(combos):
    print(f"{i+1}/{len(combos)}: {dict(zip(keys, combo))}")