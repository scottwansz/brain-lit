#!/usr/bin/env python3
"""
使用WorldQuant平台内容生成Alpha表达式的AI工具
"""

import json
import logging
import os
import sys
from typing import Dict, Any, List

# 添加项目根目录到Python路径，以便正确导入模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from ai.ask_ai import ask_dashscope

from svc.auth import get_auto_login_session
from ai.alpha_operators import alpha_operators_list
from ai.start_guide import start_guide, about_data_coverage, about_vector_type

base_url = "https://api.worldquantbrain.com"
data_fields_fetch_url = f"{base_url}/data-fields"
dataset_info_fetch_url = f"{base_url}/data-sets/"

prompt = """你是WorldQuant平台的量化策略专家。
基于以下WorldQuant平台的官方文档和资源，生成{category}类型数据集有经济学含义的高质量的Alpha表达式，生成数据不超过{count}个：
1. 什么是Alpha表达式
Alpha表达式示它是数学运算符连接的函数表达式，数据字段作为函数的参数，它来计算结果影响股票池（Universe）中各个投资标的投资占比，例如：rank(-returns)
这个表达式的假设是，我们想在明天买入或做多今天收益率为负或相对较低的股票，同时卖出或做空今天收益率为正或相对较高的股票。
1. {category}数据集Alpha生成指南：\n{start_guide}
2. 本次任务使用的数据集是{dataset}，数据集的delay是{delay}，数据集的region是{region}，数据集的universe是{universe}，该数据集的描述信息如下：\n{dataset_desc}。
3. 本次任务只能使用{dataset}数据集的如下字段：\n{data_fields_info}
4. 本次任务只能使用如下内容中指定的函数：\n{alpha_operators}
5. 字段类型为Vector时的处理参考：\n{about_vector_type}
6. 低覆盖（Coverage）率字段的处理参考：\n{about_data_coverage}

生成Alpha表达式需要满足以下要求:
2. 必须符合WorldQuant平台的语法规范
3. 应当使用平台支持的数据字段和运算符
4. 表达式应当具有经济意义和逻辑合理性
5. 特别关注情感分析相关的数据集和运算符
6. 考虑使用hump_decay, ts_decay_linear, 和 ts_decay_exp_window等操作来实现合理的保证金率
7. 仅使用WorldQuant平台实际支持的操作符和函数，参考平台文档中的alpha_operators部分定义
8. 仅使用WorldQuant平台实际可用的数据字段，参考平台文档中的data_fields部分定义，不要使用假设的字段
9. 可以使用close, returns, volume等基本价格和交易量字段，但注意returns是字段不是函数，如需计算收益应使用ts_returns函数
10. 函数参数规则：对于带有可选参数的函数，必须明确写出参数名和等号，例如hump_decay(x, p=0)不能写成hump_decay(x, 0)
11. 避免使用科学计数法（如1e-6），改用小数形式（如0.000001）
12. 不要使用不存在的操作符，如if操作符，应使用if_else操作符替代
13. 注意函数参数类型：位置参数不能使用关键字形式，可选参数必须使用关键字形式。例如ts_decay_linear(x, d)中的d是位置参数，不能写成ts_decay_linear(x, d=10)；而ts_decay_linear(x, d, dense=false)中的dense是可选参数，必须写成ts_decay_linear(x, d, dense=false)
14. 确保函数具有所需的全部参数：例如ts_rank(x, d, constant=0)至少需要x和d两个参数
15. 禁止使用如snt21_neg_mean[d=5]这样的非标准语法访问历史数据，必须使用ts_delay(snt21_neg_mean, 5)函数
16. 正确使用if_else函数，格式为if_else(condition, true_value, false_value)，例如：if_else(snt21_neg_mean > ts_delay(snt21_neg_mean, 5), -1, 1)
17. 仔细检查生成的Alpha表达式，确保所有使用的函数都在平台文档的alpha_operators部分中有明确定义
18. 只能选择平台文档中明确定义的函数

请严格按照以下格式输出，每行一个Alpha:
字段名||模板名||Alpha表达式||AI生成此Alpha的原因（因子在什么情况下产生买入或卖出信号）[英文翻译]||数据字段使用理由[英文翻译]||操作符使用理由[英文翻译]

例如:
snt21_neg_mean||负面情绪动量||ts_rank(ts_decay_linear(snt21_neg_mean, 10), 10) - ts_rank(ts_decay_exp_window(snt21_neg_mean, 5, factor=0.5), 10)||当负面情绪上升到一定程度后出现衰减时，可能预示着市场情绪反转，产生买入信号[When negative sentiment rises to a certain level and then decays, it may signal a market sentiment reversal, generating a buy signal]||使用snt21_neg_mean字段因为它是衡量市场负面情绪的关键指标[The snt21_neg_mean field is used because it is a key indicator for measuring negative market sentiment]||使用ts_decay_linear和ts_decay_exp_window操作符来比较不同衰减模式下的效果[Using ts_decay_linear and ts_decay_exp_window operators to compare effects under different decay patterns]

注意：每个理由部分都需要同时包含中文和英文翻译，格式为"中文内容[English translation]，3段英文翻译的总长度不得小于100个字符"

注意：
1. 只返回上述格式的内容，不要包含其他解释或说明
2. 每行一个Alpha表达式
3. 使用||作为分隔符
4. 生成{count}个不同的Alpha表达式
5. 确保生成的Alpha表达式具有多样性，不要重复类似的模式
6. 确保使用的数据字段是真实存在的，不要编造字段名
7. 确保函数参数数量正确，特别是hump_decay只需要两个参数
8. 避免使用科学计数法，使用小数形式
9. 避免在事件类型字段上使用ts_decay_linear函数
10. 不要使用不存在的操作符，如if操作符，应使用if_else操作符替代
11. 注意函数参数类型：位置参数不能使用关键字形式，可选参数必须使用关键字形式
12. returns是字段不是函数，如需计算收益应使用ts_returns函数
13. 确保函数具有所需的全部参数，如ts_rank至少需要两个位置参数
14. 确保if_else函数使用正确的参数格式：if_else(condition, true_value, false_value)
15. 禁止使用如snt21_neg_mean[d=5]这样的非标准语法访问历史数据，必须使用ts_delay(snt21_neg_mean, 5)函数
16. 仔细检查生成的Alpha表达式，确保所有使用的函数都在平台文档的alpha_operators部分中有明确定义
17. 每个理由部分都需要同时包含中文和英文翻译，格式为"中文内容[English translation]"
"""

def generate_alphas(
        region='IND',
        universe='TOP500',
        delay=1,
        category='sentiment',
        dataset='sentiment21',
        instrument_type='EQUITY',
        count: int = 30
) -> List[Dict[str, Any]]:
    """
    使用平台知识生成多个Alpha表达式
    
    Args:
        :param count: 生成的Alpha表达式数量
        :param instrument_type:
        :param dataset:
        :param category: 数据集类别，例如"sentiment"
        :param delay:
        :param universe:
        :param region:
    
    Returns:
        扁平结构的Alpha表达式列表
        格式: [
            {
                "field_name": "字段名",
                "template_name": "模板名", 
                "expression": "Alpha表达式",
                "reason_for_generation": "生成原因(中文)",
                "reason_for_generation_en": "生成原因(英文)",
                "data_field_rationale": "数据字段使用理由(中文)",
                "data_field_rationale_en": "数据字段使用理由(英文)",
                "operator_rationale": "操作符使用理由(中文)",
                "operator_rationale_en": "操作符使用理由(英文)"
            }
        ]
    """
    try:
        dataset_desc = get_dataset_info().get('description')
        data_fields_info = get_dataset_fields(dataset, delay, instrument_type, region=region, universe=universe)

        # 调用AI生成Alpha
        try:
            prompt_formated = prompt.format(
                region=region,
                universe=universe,
                category=category,
                delay=delay,
                dataset=dataset,
                dataset_desc=dataset_desc,
                data_fields_info=json.dumps(data_fields_info, ensure_ascii=False, indent=4),
                count=count,
                start_guide=start_guide.get(category),
                alpha_operators=json.dumps(alpha_operators_list, ensure_ascii=False, indent=4),
                about_vector_type=about_vector_type,
                about_data_coverage=about_data_coverage,
            )
            print(prompt_formated)
            response = ask_dashscope(prompt_formated)
        except Exception as e:
            logging.getLogger(__name__).error(f"AI生成Alpha表达式失败: {e}", exc_info=True)
            raise Exception(f"AI生成Alpha表达式失败: {e}")
        
        # 解析响应并组织成指定格式
        result = []
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
                    
                    result.append({
                        "field_name": field_name,
                        "template_name": template_name,
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
        return []

def get_dataset_info(dataset_id='other699'):
    session = get_auto_login_session()
    return session.get(dataset_info_fetch_url + dataset_id).json()


def get_fields_in_page(dataset_id='other699', delay=0, instrument_type='EQUITY', limit=20, offset=0, region='AMR',
                       universe='TOP600'):
    """
    获取数据字段信息，返回以id为key，type为value的字典

    Args:
        dataset_id (str): 数据集ID
        delay (int): 延迟
        instrument_type (str): 仪器类型
        limit (int): 限制返回记录数
        offset (int): 偏移量
        region (str): 地区
        universe (str): 范围

    Returns:
        dict: 以id为key，type为value的字典
    """
    # 获取自动登录会话
    session = get_auto_login_session()

    # 设置请求参数
    params = {
        'dataset.id': dataset_id,
        'delay': delay,
        'instrumentType': instrument_type,
        'limit': limit,
        'offset': offset,
        'region': region,
        'universe': universe
    }

    # 发送GET请求
    response = session.get(data_fields_fetch_url, params=params)

    # 检查响应状态
    response.raise_for_status()

    # 解析响应数据并构造以id为key，type为value的字典
    return response.json()


def get_dataset_fields(dataset='other699', delay=0, instrument_type='EQUITY', region='AMR', universe='TOP600'):
    """
    获取指定数据集的所有字段信息，返回以id为key，type为value的字典

    Args:
        dataset (str): 数据集ID
        delay (int): 延迟
        instrument_type (str): 仪器类型
        region (str): 地区
        universe (str): 范围

    Returns:
        dict: 以id为key，type为value的字典，包含数据集的所有字段
    """
    # 初始化结果字典
    result = {}

    # 分页获取所有数据
    limit = 50  # 每页获取50条记录
    offset = 0

    while True:
        # 调用现有的get_data_fields方法获取当前页数据
        batch_dict = get_fields_in_page(dataset, delay, instrument_type, limit, offset, region, universe)
        result.update(batch_dict)

        # 如果当前页返回的数据少于限制数量，说明已经到最后一页
        if len(batch_dict) < limit:
            break

        # 更新offset以获取下一页数据
        offset += limit

    return result

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
    alpha_results = generate_alphas(topic, count=count)
    
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
    # main()

    # data_fields = get_dataset_fields()
    # print(json.dumps(data_fields, ensure_ascii=False, indent=2))

    # dataset_info = get_dataset_info()
    # print(json.dumps(dataset_info, ensure_ascii=False, indent=2))
    # print(dataset_info.get("description"))

    print(f"正在生成Alpha表达式...")
    # 生成Alpha
    alpha_results = generate_alphas()
    # 输出结果
    print(f"\n生成了{len(alpha_results)}个Alpha表达式:")
    print("=" * 50)
    print(json.dumps(alpha_results[:5], ensure_ascii=False, indent=2))

    alpha_expressions = [result['expression'] for result in alpha_results]
    print(f"\n生成的Alpha表达式列表:")
    print("-" * 50)
    print(json.dumps(alpha_expressions, ensure_ascii=False, indent=2))
