import json
import logging
import os.path
import re
from typing import Optional, List

import requests

from alpha_desc.ask_ai import ask_dashscope, ai_prompt
from svc.auth import AutoLoginSession

logger = logging.getLogger(__name__)

dataset_url = 'https://api.worldquantbrain.com/data-sets'
alpha_url = 'https://platform.worldquantbrain.com/alpha'

all_operator_descriptions = json.load(open(os.path.join(os.path.dirname(__file__), 'alpha_description.json')))
# print(operator_descriptions)


def get_submitted_alphas(
        session: AutoLoginSession,
        start_date: str = "2025-08-01T04:00:00.000Z",
        end_date: str = "2025-08-07T04:00:00.000Z",
        limit: int = 10,
        offset: int = 0,
        hidden: bool = False,
        order: str = "-dateSubmitted"
) -> Optional[List[dict]]:
    """
    根据日期范围获取alphas数据

    :param session: 已登录的requests会话对象
    :param start_date: 开始日期
    :param end_date: 结束日期
    :param limit: 返回结果数量
    :param offset: 偏移量
    :param hidden: 是否包含隐藏的alphas
    :param order: 排序方式
    :return: alphas数据列表
    """

    # 构建URL参数
    base_url = "https://api.worldquantbrain.com/users/self/alphas"
    params = {
        "limit": limit,
        "offset": offset,
        "status!": "UNSUBMITTED\x1FIS-FAIL",  # 使用!而不是%21，让requests自动编码
        "dateSubmitted>": start_date,
        "dateSubmitted<": end_date,
        "order": order,
        "hidden": str(hidden).lower()
    }

    try:
        # 发送GET请求
        response = session.get(
            base_url,
            params=params,
            headers={
                "accept": "application/json;version=4.0",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
                "origin": "https://platform.worldquantbrain.com",
                "referer": "https://platform.worldquantbrain.com/",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
            }
        )

        # 检查响应状态
        response.raise_for_status()

        # 解析JSON响应
        response_json = response.json()
        alphas = response_json.get('results', [])

        # 处理分页
        while response_json.get('next'):
            next_url = response_json['next']
            # 修复URL中的问题
            next_url = next_url.replace("http://", "https://").replace(":443", "")

            response = session.get(next_url)
            response.raise_for_status()
            response_json = response.json()
            alphas.extend(response_json.get('results', []))

        return alphas

    except requests.RequestException as e:
        logging.error(f"获取alphas数据时出错: {e}", exc_info=True)
        return None


# 使用示例
def update_submitted_alphas_desc(alphas):
    if alphas is not None:

        for index, alpha in enumerate(alphas):

            logger.info(f"======= {index} {alpha.get('id')} {alpha.get('name')} ========")

            alpha_expression = alpha.get('regular').get('code')
            alpha_related_info = get_alpha_desc_related_info(session, alpha_expression, alpha_name=alpha.get('name'))

            alpha_desc = ask_dashscope(content=ai_prompt.format(alpha=alpha_expression, related_info=alpha_related_info))
            logger.info(f'\nalpha_desc generated: \n{alpha_desc}\n')

            update_brain_alpha(session, alpha_id=alpha.get('id'), alpha_name=alpha.get('name'), alpha_desc=alpha_desc)
    else:
        logger.error("alphas为空")

def update_brain_alpha(s: AutoLoginSession, alpha_id, alpha_name, alpha_desc=None):

    if not alpha_desc:
        idea = "Iterate all the combination of operations and fields in dataset to find signal quantization factors"
        rationale_of_data = "It is nonsense since it is randomly testing. Information on company's conference call, such as the type of call, the number of participants on the company side and analyst side, the number of talks/questions/sentences/paragraphs/words/chars in presentation part and Q&A part respsectively. Also it generates keywords occurrence and each position from a specific dictionary. Based on this conference call, a researcher can generate unique signals predicting sentiment on the company after the conference call event."
        rationale_of_operators = "ops rank the alpha"

        alpha_desc = f"Idea: {idea}\nRationale for data used: {rationale_of_data}\nRationale for operators used: {rationale_of_operators}"

    url = f"https://api.worldquantbrain.com/alphas/{alpha_id}"

    payload = {
        "color": None,
        "name": alpha_name,
        "tags": [],
        "category": None,
        "regular": {
            "description": alpha_desc
        }
    }

    response = s.patch(url, json=payload)

    if response.status_code != 200:
        logging.getLogger(__name__).error(f"Failed to update BRAIN alpha {alpha_id}: {response.status_code}")
        return False
    else:
        logging.getLogger(__name__).info(f"BRAIN Alpha {alpha_id} updated: {response.status_code} {alpha_name}")
        return True


def get_data_by_url(session: AutoLoginSession, url, resource_id=None):

    url = f"{url}/{resource_id if resource_id else ''}"
    response = session.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        return None

def get_data_field_info(field_name, session):

    url = f'https://api.worldquantbrain.com/data-fields/{field_name}'
    response = session.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"请求失败，状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        return None


def extract_operators_and_operands(alpha_expr):
    """
    从alpha表达式中提取操作符列表和操作数列表

    Args:
        alpha_expr (str): alpha表达式字符串

    Returns:
        tuple: (operators_list, operands_list)
    """
    # 提取操作符（函数名）
    operators = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\(', alpha_expr)

    # 提取操作数（变量名）
    # 匹配括号内的标识符，但排除函数调用（后面跟着括号的）
    operands = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)[^a-zA-Z0-9_\(]?', alpha_expr)
    operands = [op for op in operands if op not in operators and not op.isdigit()]

    # 去重并保持顺序
    unique_operands = []
    seen_operands = set()
    for operand in operands:
        if operand not in seen_operands:
            unique_operands.append(operand)
            seen_operands.add(operand)

    return operators, unique_operands


def find_operator_descriptions(operators, operator_descriptions):
    """
    在operator_description中找到与给定operators相关的条目

    Args:
        operators (list): 操作符列表
        operator_descriptions (list): 操作符描述列表

    Returns:
        dict: 包含匹配操作符信息的字典
    """
    operator_info = {}

    # 创建一个以name为键的字典以便快速查找
    descriptions_dict = {item['name']: item for item in operator_descriptions}

    for operator in operators:
        if operator in descriptions_dict:
            operator_info[operator] = descriptions_dict[operator]
        else:
            operator_info[operator] = None  # 如果未找到描述则设为None

    return operator_info


def update_single_alpha_desc_by_ai(alpha:dict[str, any], operators, fields, dataset):

    alpha_desc = ask_dashscope(content=ai_prompt.format(alpha=alpha, operators=operators, fields=fields, dataset=dataset))
    print('alpha_desc generated: ', alpha_desc)

    update_brain_alpha(session, alpha_id=alpha.get('id'), alpha_name=alpha.get('name'), alpha_desc=alpha_desc)
    logging.getLogger(__name__).info("Alpha updated successfully.")


def get_alpha_desc_related_info(session: AutoLoginSession, alpha:str, alpha_name=None):

    operators, fields = extract_operators_and_operands(alpha)
    if alpha_name:
        fields = alpha_name.split('/')
    logger.info("操作符列表: %s", operators)
    logger.info("操作数列表: %s", fields)

    # 查找操作符描述
    operator_descriptions = find_operator_descriptions(operators, all_operator_descriptions)

    field_info = get_data_field_info(fields[0], session)
    field_desc = field_info.get('description')
    dataset = field_info.get('dataset')

    dataset_info = get_data_by_url(session, dataset_url, dataset.get('id'))
    dataset_desc = dataset_info.get('description')
    dataset.update({'description': dataset_desc})

    result = {
        'operators': operator_descriptions,
        'fields': [{'id': fields[0], 'description': field_desc}],
        'dataset': dataset
    }

    logger.info("alpha_related_info: %s", result)

    return result


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - Line: %(lineno)d - %(levelname)s - %(message)s')

    session = AutoLoginSession()

    # alpha_expression = '-ts_scale(winsorize(ts_backfill(oth466_is_cogs_xdep_q, 120), std=4), 22)'
    # alpha_related_info = get_alpha_desc_related_info(session, alpha_expression)
    # print(alpha_related_info)

    start_date = "2025-08-08T04:00:00.000Z",
    end_date = "2025-08-09T04:00:00.000Z"

    alphas = get_submitted_alphas(session=session, start_date=start_date, end_date=end_date)
    logger.info(f"获取到 {len(alphas)} 个alphas")

    update_submitted_alphas_desc(alphas)
