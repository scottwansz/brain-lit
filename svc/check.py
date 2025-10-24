import json
import threading
import time
from typing import Any, Dict, List

import streamlit as st

from alpha_desc.alpha_desc_updater import update_brain_alpha_desc
from svc.alpha_query import query_checkable_alpha_details
from svc.auth import get_auto_login_session, AutoLoginSession
from svc.database import update_table
from svc.logger import setup_logger

logger = setup_logger(__name__)

@st.cache_resource
def get_check_task_manager():
    return CheckTaskManager()


class CheckTaskManager:
    def __init__(self):
        self.session = get_auto_login_session()
        self.thread = None
        self.status = {
            "stop": False,
            "passed_count": 0,
            "progress": 0,
            "status": "WAITE",
            "details": "Preparing...",
        }

    def start(self, records: List[Dict[str, Any]]):
        self.status.update({
            "stop": False,
            "passed_count": 0,
            "progress": 0,
        })

        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=check_one_batch, args=(records, self.status, self), daemon=True)
            self.thread.start()


def check_one_batch(alpha_list, task, manager=None):
    """
    检查并可能提交一批alpha策略。

    参数:
    - alpha_list: 一个包含alpha策略信息的列表。
    - s: 一个表示当前会话或状态的对象。
    - task: 一个包含任务相关信息的字典。
    - manager: CheckTaskManager实例，用于在线程结束后将self.thread设为None

    返回:
    - 是否中止: 如果任务完成(提交了4个alpha或者出现不能继续的错误)或被人为停止，则返回True，否则返回False。
    """
    # 初始化已提交计数
    passed_count = task.get('passed_count', 0)
    session = get_auto_login_session()

    task.update({
        "status": "RUNNING",
        "progress": 0,
        "passed_count": 0,
        "details": "Preparing...",
    })

    # 遍历alpha列表
    for i, record in enumerate(alpha_list):
        # 检查任务是否被停止
        if task.get('stop'):
            # 更新任务状态为停止，并返回True
            task.update({
                "status": "STOPPED",
                "details": "Stopped by user"
            })
            
            # 任务完成后将manager.thread设为None
            if manager:
                manager.thread = None
                
            return True

        if not update_brain_alpha_desc(session, record['alpha_id'], record['name']):
            continue

        # 检查alpha策略的有效性
        success, fail_reasons = check_alpha(session, record['alpha_id'], task=task)
        logger.info(f"Alpha {record['alpha_id']} check passed: {len(fail_reasons) == 0}, Fail reasons: {fail_reasons}")

        fail_reason_names = [reason.get('name') for reason in fail_reasons]
        if 'ALREADY_SUBMITTED' in fail_reason_names:
            # Alpha wrbOq51 check passed: False, Fail reasons: [{'name': 'ALREADY_SUBMITTED', 'result': 'FAIL'}]
            update_table(
                f"{record['region'].lower()}_alphas",
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
                
                # 任务完成后将manager.thread设为None
                if manager:
                    manager.thread = None
                    
                return True

            # 准备要更新的数据
            set_data = {
                'passed': 1 if len(fail_reasons) == 0 else -1,
                'fail_reasons': json.dumps(fail_reasons)
            }

            passed_count += 1 if len(fail_reasons) == 0 else 0

            # 更新数据库
            table_name = f'{record['region'].lower()}_alphas'
            update_table(table_name, {'id': record['id']}, set_data)

        # 更新任务进度
        task.update({
            "progress": round((i+1) / len(alpha_list) * 100),
            "passed_count": passed_count,
            "details": f"Processing {i+1} out of {len(alpha_list)} Alphas"
        })

    # 如果所有alphas都被处理，则返回False
    task.update({
        "status": "COMPLETED",
        "stop": True,
        "details": "All alphas checked"
    })
    
    # 任务完成后将manager.thread设为None
    if manager:
        manager.thread = None
        
    return False


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