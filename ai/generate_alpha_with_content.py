#!/usr/bin/env python3
"""
使用WorldQuant平台内容生成Alpha表达式的AI工具
"""

import json
import os
import sys
from typing import Dict, Any, List

# 添加项目根目录到Python路径，以便正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from svc.datafields import get_single_set_fields
from ai.ask_ai import ask_dashscope


def load_platform_content(dataset='sentiment21', delay=1, instrument_type='EQUITY', region='IND', universe='TOP500') -> Dict[str, Any]:
    """
    加载从WorldQuant平台获取的内容
    
    Returns:
        包含平台内容的字典
    """
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    content_file = os.path.join(project_root, 'data', 'platform_content.json')
    
    contents = {
        'data_fields': get_single_set_fields(
            dataset, delay, instrument_type, region=region, universe=universe
        ),
    }
    
    # 加载平台内容
    if os.path.exists(content_file):
        with open(content_file, 'r', encoding='utf-8') as f:
            contents.update(json.load(f))
    
    # 加载情感数据集指南
    guide_file = os.path.join(project_root, 'ai', 'sentiment_datasets_guide.txt')
    if os.path.exists(guide_file):
        with open(guide_file, 'r', encoding='utf-8') as f:
            contents['sentiment_datasets_guide'] = f.read()
    
    # 加载alpha运算符信息
    operators_file = os.path.join(project_root, 'ai', 'alpha_operators.json')
    if os.path.exists(operators_file):
        with open(operators_file, 'r', encoding='utf-8') as f:
            contents['alpha_operators'] = json.load(f)
    
    return contents


def generate_alphas_with_platform_knowledge(alpha_topic: str = "sentiment analysis", count: int = 3) -> Dict[str, Dict[str, List[str]]]:
    """
    使用平台知识生成多个Alpha表达式
    
    Args:
        alpha_topic: Alpha主题，例如"sentiment analysis"
        count: 生成的Alpha表达式数量
    
    Returns:
        按字段和模板名组织的Alpha表达式字典
        格式: {字段名: {模板名: [表达式1, 表达式2, ...]}}
    """
    try:
        # 加载平台内容
        platform_contents = load_platform_content()
        
        # 构建Prompt
        prompt = f"""
        你是WorldQuant平台的量化策略专家。基于以下WorldQuant平台的官方文档和资源，生成{count}个高质量的Alpha表达式。

        平台文档内容:
        {json.dumps(platform_contents, ensure_ascii=False, indent=2)[:10000]}  # 限制长度以避免超出token限制

        请根据以下要求生成Alpha表达式:
        1. 主题: {alpha_topic}
        2. 必须符合WorldQuant平台的语法规范
        3. 应当使用平台支持的数据字段和运算符
        4. 表达式应当具有经济意义和逻辑合理性
        5. 特别关注情感分析相关的数据集和运算符
        6. 考虑使用hump_decay, ts_decay_linear, 和 ts_decay_exp_window等操作来实现合理的保证金率
        7. 仅使用WorldQuant平台实际支持的操作符和函数，参考平台文档中的alpha_operators部分定义
        8. 仅使用WorldQuant平台实际可用的数据字段，参考平台文档中的data_fields部分定义，不要使用假设的字段
        9. 可以使用close, returns, volume等基本价格和交易量字段
        12. 函数参数规则：对于带有可选参数的函数，必须明确写出参数名和等号，例如hump_decay(x, p=0)不能写成hump_decay(x, 0)
        14. ts_decay_exp_window函数需要三个参数: ts_decay_exp_window(x, d, factor)
        15. 避免使用科学计数法（如1e-6），改用小数形式（如0.000001）
        16. ts_decay_exp_window函数的factor参数必须是整数
        17. 避免在事件类型字段上使用ts_decay_linear函数

        请严格按照以下格式输出，每行一个Alpha:
        字段名||模板名||Alpha表达式||AI生成此Alpha的原因（因子在什么情况下产生买入或卖出信号）[英文翻译]||数据字段使用理由[英文翻译]||操作符使用理由[英文翻译]
        
        例如:
        snt21_neg_mean||负面情绪动量||ts_rank(ts_decay_linear(snt21_neg_mean, 10)) - ts_rank(ts_decay_exp_window(snt21_neg_mean, 5, 3))||当负面情绪上升到一定程度后出现衰减时，可能预示着市场情绪反转，产生买入信号[When negative sentiment rises to a certain level and then decays, it may signal a market sentiment reversal, generating a buy signal]||使用snt21_neg_mean字段因为它是衡量市场负面情绪的关键指标[The snt21_neg_mean field is used because it is a key indicator for measuring negative market sentiment]||使用ts_decay_linear和ts_decay_exp_window操作符来比较不同衰减模式下的效果[Using ts_decay_linear and ts_decay_exp_window operators to compare effects under different decay patterns]
        
        注意：每个理由部分都需要同时包含中文和英文翻译，格式为"中文内容[English translation]"
        
        注意：
        1. 只返回上述格式的内容，不要包含其他解释或说明
        2. 每行一个Alpha表达式
        3. 使用||作为分隔符
        4. 生成{count}个不同的Alpha表达式
        5. 确保生成的Alpha表达式具有多样性，不要重复类似的模式
        6. 确保使用的数据字段是真实存在的，不要编造字段名
        7. 确保函数参数数量正确，特别是hump_decay只需要两个参数
        8. 避免使用科学计数法，使用小数形式
        9. ts_decay_exp_window函数的factor参数必须是整数
        10. 避免在事件类型字段上使用ts_decay_linear函数
        11. 每个理由部分都需要同时包含中文和英文翻译，格式为"中文内容[English translation]"
        """

        # 调用AI生成Alpha
        response = ask_dashscope(prompt)
        
        # 解析响应并组织成指定格式
        result = {}
        lines = response.strip().split('\n')
        
        for line in lines:
            if line.strip() and '||' in line:
                parts = line.split('||')
                if len(parts) >= 6:
                    field_name = parts[0].strip()
                    template_name = parts[1].strip()
                    alpha_expression = parts[2].strip()
                    economic_explanation = parts[3].strip()
                    data_field_rationale = parts[4].strip()
                    operator_rationale = parts[5].strip()
                    
                    # 按字段组织
                    if field_name not in result:
                        result[field_name] = {}
                    
                    # 按模板名组织
                    if template_name not in result[field_name]:
                        result[field_name][template_name] = []
                    
                    # 添加Alpha表达式及相关信息
                    reason_cn, reason_en = economic_explanation, ''
                    if '[' in economic_explanation and economic_explanation.endswith(']'):
                        parts = economic_explanation.rsplit('[', 1)
                        reason_cn = parts[0]
                        reason_en = parts[1][:-1]
                    
                    field_rationale_cn, field_rationale_en = data_field_rationale, ''
                    if '[' in data_field_rationale and data_field_rationale.endswith(']'):
                        parts = data_field_rationale.rsplit('[', 1)
                        field_rationale_cn = parts[0]
                        field_rationale_en = parts[1][:-1]
                    
                    operator_rationale_cn, operator_rationale_en = operator_rationale, ''
                    if '[' in operator_rationale and operator_rationale.endswith(']'):
                        parts = operator_rationale.rsplit('[', 1)
                        operator_rationale_cn = parts[0]
                        operator_rationale_en = parts[1][:-1]
                    
                    result[field_name][template_name].append({
                        "expression": alpha_expression,
                        "reason_for_generation": reason_cn,
                        "reason_for_generation_en": reason_en,
                        "data_field_rationale": field_rationale_cn,
                        "data_field_rationale_en": field_rationale_en,
                        "operator_rationale": operator_rationale_cn,
                        "operator_rationale_en": operator_rationale_en
                    })
        
        return result
        
    except Exception as e:
        error_msg = f"生成Alpha时发生错误: {str(e)}"
        print(error_msg, file=sys.stderr)
        # 返回空的结果格式
        return {}


def main():
    """主函数"""
    # 默认主题和数量
    topic = "sentiment analysis"
    count = 3
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        topic = sys.argv[1]
    if len(sys.argv) > 2:
        count = int(sys.argv[2])
    
    print(f"正在基于'{topic}'主题生成{count}个Alpha表达式...")
    
    # 生成Alpha
    alpha_results = generate_alphas_with_platform_knowledge(topic, count)
    
    # 输出结果
    print("\n生成的Alpha表达式:")
    print("=" * 50)
    print(json.dumps(alpha_results, ensure_ascii=False, indent=2))
    
    # 保存结果
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    output_dir = os.path.join(project_root, 'data')
    output_path = os.path.join(output_dir, f"generated_alphas_{topic.replace(' ', '_')}.json")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(alpha_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {output_path}")


if __name__ == "__main__":
    main()