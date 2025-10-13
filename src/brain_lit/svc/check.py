import json
import threading

import streamlit as st
import time

from brain_lit.logger import setup_logger
from brain_lit.svc.submit import submit_alpha
from brain_lit.alpha_desc.alpha_desc_updater import get_alpha_desc_related_info, update_brain_alpha
from brain_lit.alpha_desc.ask_ai import ask_dashscope, ai_prompt
from brain_lit.svc.auth import AutoLoginSession, get_auto_login_session
from brain_lit.svc.alpha_query import query_submittable_alpha_details
from brain_lit.svc.database import update_table

logger = setup_logger(__name__)

@st.cache_resource
def get_check_and_submit_task_manager():
    return CheckAndSubmitTaskManager()


class CheckAndSubmitTaskManager:
    def __init__(self):
        self.session = get_auto_login_session()
        self.status = {
            "stop": False,
            "submitted_count": 0,
            "progress": 0,
            "status": "WAITE",
            "details": "Preparing...",
        }

    def start(self, query: dict):
        self.status.update({
            "stop": False,
            "query": query,
        })
        thread = threading.Thread(target=check_by_query, args=(self.status,), daemon=True)
        thread.start()


# def update_brain_alpha(s: AutoLoginSession, alpha_name, alpha_id, alpha_desc=None):
#     if not alpha_desc:
#         idea = "Iterate all the combination of operations and fields in dataset to find signal quantization factors"
#         rationale_of_data = "It is nonsense since it is randomly testing. Information on company's conference call, such as the type of call, the number of participants on the company side and analyst side, the number of talks/questions/sentences/paragraphs/words/chars in presentation part and Q&A part respsectively. Also it generates keywords occurrence and each position from a specific dictionary. Based on this conference call, a researcher can generate unique signals predicting sentiment on the company after the conference call event."
#         rationale_of_operators = "ops rank the alpha"
#
#         alpha_desc = f"Idea: {idea}\nRationale for data used: {rationale_of_data}\nRationale for operators used: {rationale_of_operators}"
#
#     url = f"https://api.worldquantbrain.com/alphas/{alpha_id}"
#     payload = {
#         "color": None,
#         "name": alpha_name,
#         "tags": [],
#         "category": None,
#         "regular": {
#             "description": alpha_desc
#         }
#     }
#     response = s.patch(url, json=payload)
#     if response.status_code != 200:
#         logging.getLogger(__name__).error(f"Failed to update BRAIN alpha {alpha_id}: {response.status_code}")
#         return False
#     else:
#         logging.getLogger(__name__).info(f"BRAIN Alpha {alpha_id} updated: {response.status_code} {alpha_name}")
#         return True


def check_alpha(s: AutoLoginSession, alpha_id, task:dict):
    url = f"https://api.worldquantbrain.com/alphas/{alpha_id}/check"
    time_start = time.time()

    response = s.get(url)
    logger.info(f"Alpha {alpha_id} check status: {response.status_code}")

    try_count = 0
    while response.status_code == 504:
        try_count += 1
        logger.warning(f"504 Gateway Timeout for CHECK. Retrying...{try_count}")
        time.sleep(1)
        response = s.get(url)
        if try_count > 3:
            return False, [{'name': '504_GATEWAY_TIMEOUT'}]

    while "retry-after" in response.headers and not task.get('stop'):

        if task.get('stop'):
            return False, [{'name': 'STOPPED_BY_USER'}]

        logger.info(f"Alpha {alpha_id} is checking. Waiting...  {round(time.time() - time_start)}")
        time.sleep(60) # float(response.headers["Retry-After"])
        response = s.get(url)

    if response.status_code == 200:
        try:
            data = response.json()
            # 解析检查结果
            checks = data.get('is', {}).get('checks', [])
            # passed = all(item["result"] == "PASS" for item in checks)
            fail_reasons = [check for check in checks if check.get('result') == 'FAIL']

            return True, fail_reasons
        except json.JSONDecodeError:
            logger.error(f"Failed to parse response for alpha {alpha_id}")
            return False, [{'name': 'JSON_DECODE_ERROR'}]
    else:
        logger.error(f"Failed to check alpha {alpha_id} status_code: {response.status_code}")
        logger.error(f"Failed to check alpha {alpha_id} response content: {response.content.decode('utf-8') if response.content else 'Empty response'}")
        return False, [{'name': f'{response.status_code}_ERROR'}]


def check_by_query(task:dict):

    task.update({
        "batch": 0,
        "status": "RUNNING",
        "progress": 0,
        "details": "Preparing...",
    })

    region = task.get('query').get('region', 'USA')

    while not task.get('stop'):

        task.update({
            "batch": task.get('batch', 0) + 1,
            "progress": 0,
            "details": "Preparing...",
        })

        alpha_list = query_submittable_alpha_details(**task.get('query'))

        if len(alpha_list) > 0:
            check_one_batch(region, alpha_list, task)
        else:
            task.update({
                "status": "COMPLETED",
                "stop": True,
                "details": "No more alphas to check"
            })

    task.update({
        "status": "COMPLETED",
    })


def check_one_batch(region, alpha_list, task):
    """
    检查并可能提交一批alpha策略。

    参数:
    - region: 区域标识，用于指定操作的区域。
    - alpha_list: 一个包含alpha策略信息的列表。
    - s: 一个表示当前会话或状态的对象。
    - task: 一个包含任务相关信息的字典。

    返回:
    - 是否中止: 如果任务完成(提交了4个alpha或者出现不能继续的错误)或被人为停止，则返回True，否则返回False。
    """
    # 初始化已提交计数
    submitted_count = task.get('submitted_count', 0)
    session = get_auto_login_session()

    # 遍历alpha列表
    for i, record in enumerate(alpha_list):
        # 检查任务是否被停止
        if task.get('stop'):
            # 更新任务状态为停止，并返回True
            task.update({
                "status": "STOPPED",
                "details": "Stopped by user"
            })
            return True

        if not update_brain_alpha(session, record['alpha_id'], record['name']):
            continue

        # 检查alpha策略的有效性
        success, fail_reasons = check_alpha(session, record['alpha_id'], task=task)
        logger.info(f"Alpha {record['alpha_id']} check passed: {len(fail_reasons) == 0}, Fail reasons: {fail_reasons}")

        fail_reason_names = [reason.get('name') for reason in fail_reasons]
        if 'ALREADY_SUBMITTED' in fail_reason_names:
            # Alpha wrbOq51 check passed: False, Fail reasons: [{'name': 'ALREADY_SUBMITTED', 'result': 'FAIL'}]
            update_table(
                f"{region.lower()}_alphas",
                {'alpha_id': record['alpha_id']},
                {'passed': 1, 'submitted': 1}
            )
            continue

        if success:
            # 检查是否达到常规提交限制 [{'name': 'D0_SUBMISSION', 'result': 'FAIL', 'limit': 30, 'value': 30}, {'name': 'REGULAR_SUBMISSION', 'result': 'FAIL', 'limit': 4, 'value': 4}]
            submission_limits = ['D0_SUBMISSION', 'REGULAR_SUBMISSION']
            if any(reason.get('name') in submission_limits and reason.get('result') == 'FAIL' for reason in fail_reasons):
            # if fail_reasons == [{'name': 'REGULAR_SUBMISSION', 'result': 'FAIL', 'limit': 4, 'value': 4}]:
                logger.warning("SUBMISSION limit reached, breaking...")
                task.update({
                    "status": "COMPLETED",
                    "stop": True,
                    "details": "SUBMISSION limit reached"
                })
                return True

            # 准备要更新的数据
            set_data = {
                'passed': 1 if len(fail_reasons) == 0 else -1,
                'fail_reasons': json.dumps(fail_reasons)
            }

            # 更新数据库
            table_name = f'{region.lower()}_alphas'
            update_table(table_name, {'id': record['id']}, set_data)

            # 如果没有失败原因，则尝试提交alpha策略
            if len(fail_reasons) == 0:
                success, error = submit_alpha(session, record['alpha_id'], region)
                if success:

                    alpha_related_info = get_alpha_desc_related_info(session, record['alpha'])
                    alpha_desc = ask_dashscope(content=ai_prompt.format(alpha=record['alpha'], related_info=alpha_related_info))
                    print(f'\nalpha_desc generated: \n{alpha_desc}\n')

                    update_brain_alpha(session, alpha_id=record.get('alpha_id'), alpha_name=record.get('name'),
                                       alpha_desc=alpha_desc)

                    submitted_count += 1
                    task.update({
                        "submitted_count": submitted_count,
                    })
                    if submitted_count >= 4:
                        return True
                else:
                    if error in ['REGULAR_SUBMISSION_LIMIT']:
                        logger.warning("SUBMISSION limit reached, breaking...")
                        task.update({
                            "details": "SUBMISSION limit reached",
                        })
                        return True

        # 更新任务进度
        task.update({
            "progress": round((i+1) / len(alpha_list) * 100),
            "details": f"Processing {i+1} out of {len(alpha_list)} Alphas"
        })

    # 如果所有alphas都被处理，则返回False
    return False

