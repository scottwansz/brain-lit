import logging

import requests
import streamlit as st
from openai import OpenAI

# ai_prompt = """WorldQuant Brain is a web-based tool for backtesting trading ideas. An Alpha is a concrete trading idea that can be simulated historically.
# In Brain, an 'Alpha' refers to a mathematical model, written as an expression, which places different bets (weights) on different instruments (stocks), and is expected to be profitable in the long run. After a user enters an Alpha expression that consists of dataset fields, operators and constants, the input code is evaluated for each instrument to construct a portfolio. Then BRAIN makes investments in each instrument for a one-day period in proportion to the values of the expression. The process repeats each day.
# To find a signal quantization factor, I algorithmically traverse all combinations of fields and operators in all datasets on the WorldQuant Brain platform and find the following alpha:
#
# alpha: {alpha}
# operators in this alpha: {operators}
# fields in this alpha: {fields}
# dataset of this alpha: {dataset}
#
# Generate description of the alpha following the template as below, 3 sentences, 100 character minimum totally:
# Idea: [idea]
# Rationale for data used: [reason_use_this_data]
# Rationale for operators used: [reason_use_these_operators]"""

ai_prompt = """WorldQuant Brain is a web-based tool for backtesting trading ideas. An Alpha is a concrete trading idea that can be simulated historically.
In Brain, an 'Alpha' refers to a mathematical model, written as an expression, which places different bets (weights) on different instruments (stocks), and is expected to be profitable in the long run. After a user enters an Alpha expression that consists of dataset fields, operators and constants, the input code is evaluated for each instrument to construct a portfolio. Then BRAIN makes investments in each instrument for a one-day period in proportion to the values of the expression. The process repeats each day.
To find a signal quantization factor, I algorithmically iterate all combinations of fields and operators in all datasets on the WorldQuant Brain platform and find the following alpha:

alpha: {alpha}
this alpha related information, including operators, fields, dataset: {related_info}

Generate description of the alpha following the template as below, 3 sentences, 100 character minimum totally:
Idea: [idea]
Rationale for data used: [reason_use_this_data]
Rationale for operators used: [reason_use_these_operators]"""

def ask_local_ai():
    global headers
    # 定义请求的 URL
    url = "http://localhost:12434/engines/llama.cpp/v1/chat/completions"
    # 定义请求头
    headers = {
        "Content-Type": "application/json"
    }
    # 定义请求体数据
    data = {
        "model": "ai/smollm2:latest",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Please write 500 words about the fall of Rome."
            }
        ]
    }
    # 发送 POST 请求
    response = requests.post(url, headers=headers, json=data)
    # 输出响应内容
    print(response.text)


def ask_dashscope(content="你是谁？"):

    client = OpenAI(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key = st.secrets["openai"]["DASHSCOPE_API_KEY"],
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # logging.getLogger(__name__).info(f"Asking DashScope: {content}")

    completion = client.chat.completions.create(
        # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": content},
        ],
        # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
        # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
        # extra_body={"enable_thinking": False},
    )

    # logging.getLogger(__name__).info(completion.model_dump_json())

    # 直接从 completion 对象中提取助手消息
    if hasattr(completion, 'choices') and len(completion.choices) > 0:
        return completion.choices[0].message.content.strip()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - Line: %(lineno)d')

    alpha_expression = '-ts_scale(winsorize(ts_backfill(oth466_is_cogs_xdep_q, 120), std=4), 22)'
    alpha_related_info = {'operator_descriptions': {'ts_scale': {'name': 'ts_scale', 'category': 'Time Series', 'scope': ['COMBO', 'REGULAR'], 'definition': 'ts_scale(x, d, constant = 0)', 'description': 'Returns (x - ts_min(x, d)) / (ts_max(x, d) - ts_min(x, d)) + constant. This operator is similar to scale down operator but acts in time series space', 'documentation': '/operators/ts_scale', 'level': 'ALL'}, 'winsorize': {'name': 'winsorize', 'category': 'Cross Sectional', 'scope': ['COMBO', 'REGULAR'], 'definition': 'winsorize(x, std=4)', 'description': 'Winsorizes x to make sure that all values in x are between the lower and upper limits, which are specified as multiple of std.', 'documentation': None, 'level': 'ALL'}, 'ts_backfill': {'name': 'ts_backfill', 'category': 'Time Series', 'scope': ['COMBO', 'REGULAR'], 'definition': 'ts_backfill(x,lookback = d, k=1, ignore="NAN")', 'description': 'Backfill is the process of replacing the NAN or 0 values by a meaningful value (i.e., a first non-NaN value)', 'documentation': '/operators/ts_backfill', 'level': 'ALL'}}, 'fields': [{'id': 'oth466_is_cogs_xdep_q', 'description': 'COGS excluding D&A'}], 'dataset': {'id': 'other466', 'name': 'Aggregated Fundamental Data ', 'description': 'Combines different fundamental datafields by aggregating data fields from many vendors. '}}

    # ai_prompt = ai_prompt.format(alpha=alpha_expression, operators=alpha_related_info.get('operators'), fields=alpha_related_info.get('fields'), dataset=alpha_related_info.get('dataset'))
    ai_prompt = ai_prompt.format(alpha=alpha_expression, related_info=alpha_related_info)

    print(ask_dashscope(ai_prompt))
