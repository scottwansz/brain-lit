from gen.phase2_gen import get_phase1_alphas, get_group_second_order_factory

if __name__ == '__main__':
    region = "EUR"
    group_ops = ["group_neutralize", "group_rank", "group_zscore"]

    new_records = []
    records = get_phase1_alphas(region)
    print(len( records))

    for r in records:
        expr = r['alpha']
        for alpha in get_group_second_order_factory([expr], group_ops, region):
            new_record = r.copy()
            new_record['alpha'] = alpha
            new_record['phase'] = 2
            new_record['template'] = 'phase2'
            new_record['simulated'] = 0
            new_record['used'] = 2
            new_records.append(new_record)

    for r in new_records[:10]:
        print(r)

    print(len(new_records))