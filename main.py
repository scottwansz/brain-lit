from gen.sentiment_gen import SentimentAlphaGeneratorV5
from svc.datafields import get_single_set_fields


# 主程序
def main():
    """主程序：生成所有Alpha表达式"""
    print("=" * 80)
    print("情感数据Alpha表达式生成器 V5")
    print("=" * 80)

    # 使用示例数据（替换为您的实际数据）
    data_fields = get_single_set_fields(
        region="IND",
        universe="TOP500",
        instrument_type="EQUITY",
        delay=1,
        dataset="sentiment23",
    )

    # 创建生成器
    print("\n初始化生成器...")
    generator = SentimentAlphaGeneratorV5(field_metadata=data_fields)

    # 导出所有策略
    print("\n生成所有Alpha表达式...")
    print("=" * 80)

    all_strategies = generator.export_all_strategies(
        output_format="json",
        include_full_pipeline=True
    )

    # 保存到文件
    with open('data/all_sentiment_alphas.json', 'w', encoding='utf-8') as f:
        f.write(all_strategies)

    print(f"\n已生成所有Alpha表达式，保存到 all_sentiment_alphas.json")

    # # 同时生成Python版本
    # python_strategies = generator.export_all_strategies(
    #     output_format="python",
    #     include_full_pipeline=True
    # )
    #
    # with open('data/all_sentiment_alphas.py', 'w', encoding='utf-8') as f:
    #     f.write(python_strategies)
    #
    # print(f"Python版本已保存到 all_sentiment_alphas.py")

    # 显示统计信息
    print("\n" + "=" * 80)
    print("生成统计信息:")
    print("=" * 80)

    # 读取生成的JSON获取统计信息
    import json
    data = json.loads(all_strategies)

    print(f"总字段数: {data['meta']['total_fields']}")
    print(f"完整组数: {data['meta']['complete_groups']}")
    print(f"总策略数: {data['meta']['strategy_count']}")
    
    # 计算总的Alpha表达式数量
    total_expressions = sum(len(strategy_data['alpha_expressions']) for strategy_data in data['strategies'].values())
    print(f"总Alpha表达式数: {total_expressions}")

    print(f"\n可用统计类型: {', '.join(data['meta']['available_stat_types'])}")
    print(f"可用窗口: {', '.join(data['meta']['available_windows'])}")

    # 按策略显示分组数量
    print(f"\n各策略分组分布:")
    strategy_counts = {}
    for strategy_name, strategy_data in data["strategies"].items():
        count = len(strategy_data["alpha_expressions"])
        strategy_counts[strategy_name] = count

    # 按分组数量排序
    sorted_counts = sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True)

    for strategy_name, count in sorted_counts[:10]:  # 显示前10个
        print(f"  {strategy_name}: {count} 个分组")

    if len(sorted_counts) > 10:
        print(f"  ... 还有 {len(sorted_counts) - 10} 个策略")

    # 显示一些示例
    print("\n" + "=" * 80)
    print("示例策略:")
    print("=" * 80)

    # 获取第一个策略
    first_strategy_name = list(data["strategies"].keys())[0]
    first_strategy = data["strategies"][first_strategy_name]

    print(f"策略: {first_strategy_name}")
    print(f"类型: {first_strategy['type']}")
    if "description" in first_strategy:
        print(f"描述: {first_strategy['description']}")
    if "base_strategy" in first_strategy:
        print(f"基础策略: {first_strategy['base_strategy']}")
    print(f"分组数量: {len(first_strategy['alpha_expressions'])}")
    
    # 显示第一个策略的第一个表达式
    first_group_key = list(first_strategy['alpha_expressions'].keys())[0]
    first_expression = first_strategy['alpha_expressions'][first_group_key]
    print(f"示例表达式 ({first_group_key}):\n{first_expression}")

    # 显示一个行业中性化的示例
    print("\n" + "=" * 80)
    print("行业中性化示例:")
    print("=" * 80)

    # 查找行业中性化的策略
    industry_neutralized_found = False
    for strategy_name, strategy_data in data["strategies"].items():
        if "industry_neutralized" in strategy_name:
            print(f"策略: {strategy_name}")
            print(f"类型: {strategy_data['type']}")
            if "description" in strategy_data:
                print(f"描述: {strategy_data['description']}")
            if "base_strategy" in strategy_data:
                print(f"基础策略: {strategy_data['base_strategy']}")
            
            # 显示一个表达式示例
            first_group_key = list(strategy_data['alpha_expressions'].keys())[0]
            first_expression = strategy_data['alpha_expressions'][first_group_key]
            print(f"示例表达式 ({first_group_key}):\n{first_expression}")
            industry_neutralized_found = True
            break

    if not industry_neutralized_found:
        print("未找到行业中性化策略示例")

    print("\n" + "=" * 80)
    print("生成完成！")
    print("=" * 80)


# 运行主程序
if __name__ == "__main__":
    main()