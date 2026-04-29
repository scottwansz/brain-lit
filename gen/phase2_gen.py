
def group_factory(op, field, region):
    output = []
    vectors = ["cap"]

    # chn_group_13 = ['pv13_di_2l', 'pv13_di_1l', 'pv13_parent']  # 'pv13_di_4l',  'pv13_di_3l', 'pv13_h_min2_sector', 'pv13_di_6l', 'pv13_rcsed_6l', 'pv13_di_5l', , 'pv13_level'

    chn_group_1 = ['sta1_top3000c30', 'sta1_top3000c20', 'sta1_top3000c10', 'sta1_top3000c2', 'sta1_top3000c5']

    # chn_group_2 = ['sta2_top3000_fact3_c20']  # 'sta2_top3000_fact4_c10', 'sta2_top2000_fact4_c50',

    hkg_group_13 = ['pv13_10_f3_g2_minvol_1m_sector', 'pv13_10_minvol_1m_sector', 'pv13_20_minvol_1m_sector',
                    'pv13_2_minvol_1m_sector', 'pv13_5_minvol_1m_sector', 'pv13_1l_scibr', 'pv13_3l_scibr',
                    'pv13_2l_scibr', 'pv13_4l_scibr', 'pv13_5l_scibr']

    hkg_group_1 = ['sta1_allc50', 'sta1_allc5', 'sta1_allxjp_513_c20', 'sta1_top2000xjp_513_c5']

    hkg_group_2 = ['sta2_all_xjp_513_all_fact4_c10', 'sta2_top2000_xjp_513_top2000_fact3_c10',
                   'sta2_allfactor_xjp_513_13', 'sta2_top2000_xjp_513_top2000_fact3_c20']

    twn_group_13 = ['pv13_2_minvol_1m_sector', 'pv13_20_minvol_1m_sector', 'pv13_10_minvol_1m_sector',
                    'pv13_5_minvol_1m_sector', 'pv13_10_f3_g2_minvol_1m_sector', 'pv13_5_f3_g2_minvol_1m_sector',
                    'pv13_2_f4_g3_minvol_1m_sector']

    twn_group_1 = ['sta1_allc50', 'sta1_allxjp_513_c50', 'sta1_allxjp_513_c20', 'sta1_allxjp_513_c2',
                   'sta1_allc20', 'sta1_allxjp_513_c5', 'sta1_allxjp_513_c10', 'sta1_allc2', 'sta1_allc5']

    twn_group_2 = ['sta2_allfactor_xjp_513_0', 'sta2_all_xjp_513_all_fact3_c20',
                   'sta2_all_xjp_513_all_fact4_c20', 'sta2_all_xjp_513_all_fact4_c50']

    usa_group_13 = ['pv13_h_min2_3000_sector', 'pv13_r2_min20_3000_sector', 'pv13_r2_min2_3000_sector',
                    'pv13_r2_min2_3000_sector', 'pv13_h_min2_focused_pureplay_3000_sector']

    usa_group_1 = ['sta1_top3000c50', 'sta1_allc20', 'sta1_allc10', 'sta1_top3000c20', 'sta1_allc5']

    usa_group_2 = ['sta2_top3000_fact3_c50', 'sta2_top3000_fact4_c20', 'sta2_top3000_fact4_c10']

    usa_group_6 = ['mdl10_group_name']

    asi_group_13 = ['pv13_20_minvol_1m_sector', 'pv13_5_f3_g2_minvol_1m_sector', 'pv13_10_f3_g2_minvol_1m_sector',
                    'pv13_2_f4_g3_minvol_1m_sector', 'pv13_10_minvol_1m_sector', 'pv13_5_minvol_1m_sector']

    asi_group_1 = ['sta1_allc50', 'sta1_allc10', 'sta1_minvol1mc50', 'sta1_minvol1mc20',
                   'sta1_minvol1m_normc20', 'sta1_minvol1m_normc50']

    jpn_group_1 = ['sta1_alljpn_513_c5', 'sta1_alljpn_513_c50', 'sta1_alljpn_513_c2', 'sta1_alljpn_513_c20']

    jpn_group_2 = ['sta2_top2000_jpn_513_top2000_fact3_c20', 'sta2_all_jpn_513_all_fact1_c5',
                   'sta2_allfactor_jpn_513_9', 'sta2_all_jpn_513_all_fact1_c10']

    jpn_group_13 = ['pv13_2_minvol_1m_sector', 'pv13_2_f4_g3_minvol_1m_sector', 'pv13_10_minvol_1m_sector',
                    'pv13_10_f3_g2_minvol_1m_sector', 'pv13_all_delay_1_parent', 'pv13_all_delay_1_level']

    kor_group_13 = ['pv13_10_f3_g2_minvol_1m_sector', 'pv13_5_minvol_1m_sector', 'pv13_5_f3_g2_minvol_1m_sector',
                    'pv13_2_minvol_1m_sector', 'pv13_20_minvol_1m_sector', 'pv13_2_f4_g3_minvol_1m_sector']

    kor_group_1 = ['sta1_allc20', 'sta1_allc50', 'sta1_allc2', 'sta1_allc10', 'sta1_minvol1mc50',
                   'sta1_allxjp_513_c10', 'sta1_top2000xjp_513_c50']

    kor_group_2 = ['sta2_all_xjp_513_all_fact1_c50', 'sta2_top2000_xjp_513_top2000_fact2_c50',
                   'sta2_all_xjp_513_all_fact4_c50', 'sta2_all_xjp_513_all_fact4_c5']

    eur_group_13 = ['pv13_5_sector', 'pv13_2_sector', 'pv13_v3_3l_scibr', 'pv13_v3_2l_scibr', 'pv13_2l_scibr',
                    'pv13_52_sector', 'pv13_v3_6l_scibr', 'pv13_v3_4l_scibr', 'pv13_v3_1l_scibr']

    eur_group_1 = ['sta1_allc10', 'sta1_allc2', 'sta1_top1200c2', 'sta1_allc20', 'sta1_top1200c10']

    eur_group_2 = ['sta2_top1200_fact3_c50', 'sta2_top1200_fact3_c20', 'sta2_top1200_fact4_c50']

    glb_group_13 = ["pv13_10_f2_g3_sector", "pv13_2_f3_g2_sector", "pv13_2_sector", "pv13_52_all_delay_1_sector"]

    glb_group_1 = ['sta1_allc20', 'sta1_allc10', 'sta1_allc50', 'sta1_allc5']

    glb_group_2 = ['sta2_all_fact4_c50', 'sta2_all_fact4_c20', 'sta2_all_fact3_c20', 'sta2_all_fact4_c10']

    glb_group_13 = ['pv13_2_sector', 'pv13_10_sector', 'pv13_3l_scibr', 'pv13_2l_scibr', 'pv13_1l_scibr',
                    'pv13_52_minvol_1m_all_delay_1_sector', 'pv13_52_minvol_1m_sector', 'pv13_52_minvol_1m_sector']

    amr_group_13 = ['pv13_4l_scibr', 'pv13_1l_scibr', 'pv13_hierarchy_min51_f1_sector',
                    'pv13_hierarchy_min2_600_sector', 'pv13_r2_min2_sector', 'pv13_h_min20_600_sector']

    # bps_group = "bucket(rank(fnd28_value_05480), range='0.1, 1, 0.1')"
    # pb_group = "bucket(rank(close/fnd28_value_05480), range='0.1, 1, 0.1')"
    cap_group = "bucket(rank(cap), range='0.1, 1, 0.1')"
    asset_group = "bucket(rank(assets),range='0.1, 1, 0.1')"
    sector_cap_group = "bucket(group_rank(cap, sector),range='0.1, 1, 0.1')"
    sector_asset_group = "bucket(group_rank(assets, sector),range='0.1, 1, 0.1')"

    vol_group = "bucket(rank(ts_std_dev(returns,20)),range = '0.1, 1, 0.1')"

    liquidity_group = "bucket(rank(close*volume),range = '0.1, 1, 0.1')"

    groups = ["market", "sector", "industry", "subindustry",
              cap_group, asset_group, sector_cap_group, sector_asset_group, vol_group,
              liquidity_group]  # pb_group, bps_group,

    if region == "CHN":
        groups += chn_group_1  # + chn_group_13 + chn_group_2
    if region == "TWN":
        groups += twn_group_13 + twn_group_1 + twn_group_2
    if region == "ASI":
        groups += asi_group_13 + asi_group_1
    if region == "USA":
        groups += usa_group_13 + usa_group_1 + usa_group_2
    if region == "HKG":
        groups += hkg_group_13 + hkg_group_1 + hkg_group_2
    if region == "KOR":
        groups += kor_group_13 + kor_group_1 + kor_group_2
    if region == "EUR":
        groups += eur_group_13 + eur_group_1 + eur_group_2
    if region == "GLB":
        groups += glb_group_13 + glb_group_1 + glb_group_2
    if region == "AMR":
        groups += amr_group_13
    if region == "JPN":
        groups += jpn_group_1 + jpn_group_2 + jpn_group_13

    for group in groups:
        if op.startswith("group_vector"):
            for vector in vectors:
                alpha = "%s(%s,%s,densify(%s))" % (op, field, vector, group)
                output.append(alpha)
        elif op.startswith("group_percentage"):
            alpha = "%s(%s,densify(%s),percentage=0.5)" % (op, field, group)
            output.append(alpha)
        else:
            alpha = "%s(%s,densify(%s))" % (op, field, group)
            output.append(alpha)

    return output

def get_group_second_order_factory(first_order, group_ops, region):
    second_order = []
    for fo in first_order:
        for group_op in group_ops:
            second_order += group_factory(group_op, fo, region)
    return second_order


def get_phase1_alphas(param):
    return [
        "ts_sum(ts_backfill(vec_avg(avg_rest_time_ask_cancelled_lvl1), 250), 5)",
        "-ts_std_dev(ts_backfill(vec_avg(filled_ebbo_order_count), 250), 5)",
    ]


if __name__ == '__main__':
    region = "EUR"
    expr = get_phase1_alphas(region)
    group_ops = ["group_neutralize", "group_rank", "group_zscore"]
    so_alpha_list = []

    for alpha in get_group_second_order_factory([expr], group_ops, region):
        so_alpha_list.append(alpha)

    for alpha in so_alpha_list:
        print(alpha)
