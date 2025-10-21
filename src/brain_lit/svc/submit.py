import logging
import threading
from typing import Any, List, Dict

import streamlit as st
import time
import json

from brain_lit.alpha_desc.alpha_desc_updater import get_alpha_desc_related_info, update_brain_alpha
from brain_lit.alpha_desc.ask_ai import ask_dashscope, ai_prompt
from brain_lit.logger import setup_logger
from brain_lit.svc.auth import AutoLoginSession, get_auto_login_session
from brain_lit.svc.database import update_table, query_table

logger = setup_logger(__name__)

@st.cache_resource
def get_submit_task_manager():
    return SubmitTaskManager()


class SubmitTaskManager:
    def __init__(self):
        self.session = get_auto_login_session()
        self.thread = None
        self.status = {
            "stop": False,
            "submitted_count": 0,
            "progress": 0,
            "status": "WAITE",
            "details": "Preparing...",
        }

    def start(self, records:List[Dict[str, Any]]):
        self.status.update({
            "stop": False,
        })

        thread = threading.Thread(target=submit_task, args=(records, self.status,), daemon=True)
        thread.start()

def submit_task(records: List[Dict[str, Any]], status: Dict[str, Any]):

    submitted_count = status.get("submitted_count", 0)
    session = get_auto_login_session()

    for record in records:
        success, error = submit_alpha(session, record['alpha_id'], record['region'])

        submitted_count += 1
        status.update({
            "submitted_count": submitted_count,
        })

        if success:

            alpha_related_info = get_alpha_desc_related_info(session, record['alpha'])
            alpha_desc = ask_dashscope(content=ai_prompt.format(alpha=record['alpha'], related_info=alpha_related_info))
            print(f'\nalpha_desc generated: \n{alpha_desc}\n')

            update_brain_alpha(session, alpha_id=record.get('alpha_id'), alpha_name=record.get('name'),
                               alpha_desc=alpha_desc)

            if submitted_count >= 4:
                return True
        else:
            logger.error(f"Failed to submit alpha {record.get('alpha_id')}: {error}")
            status.update({
                "details": error,
            })

            if error in ['REGULAR_SUBMISSION_LIMIT']:
                logger.warning("SUBMISSION limit reached, breaking...")
                return True
    return None


def get_submitted_alphas_brain(s: AutoLoginSession):
    result = []
    done = False

    # url_params = {
    #     'limit': 10,
    #     'offset': 0,
    #     'status!': 'UNSUBMITTEDIS-FAIL',
    #     'order': '-dateSubmitted',
    #     'hidden': 'false'
    # }

    url = "https://api.worldquantbrain.com:443/users/self/alphas?hidden=false&limit=100&offset=0&order=-dateSubmitted&status%21=UNSUBMITTED%1FIS-FAIL"

    while not done:
        print(f"Fetching alphas from {url}...")
        response = s.get(url)

        if response.status_code == 200:
            result.extend(response.json().get("results"))

            if response.json().get("next"):
                next_url = response.json().get("next")
                # 确保next_url使用HTTPS协议
                if not next_url.startswith("https"):
                    next_url = next_url.replace("http", "https", 1)
                url = next_url
            else:
                done = True

        elif response.status_code == 400:
            logging.getLogger(__name__).error(f"Bad request: {response.status_code} - {response.text}")
            return None
        else:
            logging.getLogger(__name__).error(f"Failed to fetch alphas: {response.status_code} - {response.text}")
            return None

    return result


def submit_alpha(s: AutoLoginSession, alpha_id, region):

    error_reached_quota = {"name": "REGULAR_SUBMISSION", "result": "FAIL", "limit": 4, "value": 4}  # Alpha submissions 4 reached quota of 4.
    error_already_submitted = {"name": "ALREADY_SUBMITTED", "result": "FAIL"}
    error_throttled = {"detail": "THROTTLED"}

    url = f"https://api.worldquantbrain.com/alphas/{alpha_id}/submit"

    response = s.post(url)  # response.status_code 201 and no response.json()
    logger.info(f"Submit alpha {alpha_id} status code %s: %s", response.status_code, response.text)
    # print(url, response.status_code, response.text)
    # 400 Bad Request 其它程序正在提交中
    # 403 Forbidden error_reached_quota

    n_retry = 0
    while response.status_code == 504 and n_retry < 3:
        time.sleep(10)
        n_retry += 1
        logger.warning(f"504 Gateway Time-out. Retrying submit alpha {alpha_id}... {n_retry}")
        response = s.post(url)

    if response.status_code == 201:
        time_start = time.time()
        response = s.get(url)

        while "retry-after" in response.headers:
            time.sleep(60)  # float(response.headers["Retry-After"])
            logger.info(f'Submitting alpha {alpha_id}... time used: {round(time.time() - time_start)}.')
            response = s.get(url)

    success = False
    error = 'UNKNOWN'

    if response.status_code == 200:
        logger.info(f"Alpha {alpha_id} submitted successfully.")
        table_name = f"{region.lower()}_alphas"
        update_table(table_name, {'alpha_id': alpha_id}, {'submitted': 1})
        success = True

    else:
        logger.error(f"Failed to submit alpha {alpha_id}: {response.status_code} - {response.text}")
        # 404
        # 504 Gateway Time-out

        if response.status_code == 403:

            checks = response.json().get('is', {}).get('checks', [])

            if error_reached_quota in checks:
                error = 'REGULAR_SUBMISSION_LIMIT'

            elif error_already_submitted in checks:
                error = 'ALREADY_SUBMITTED'
                update_table(f"{region.lower()}_alphas", {'alpha_id': alpha_id}, {'submitted': 1})

            else:
                # 检查未通过的情形，如sharp值小于1.58
                fail_reasons = [check for check in checks if check.get('result') == 'FAIL']
                set_data = {
                    'passed': 1 if len(fail_reasons) == 0 else -1,
                    'fail_reasons': json.dumps(fail_reasons)
                }

                update_table(f"{region.lower()}_alphas", {'alpha_id': alpha_id}, set_data)
                error = 'CHECK_FAIL'

        elif response.status_code == 429:  # Too Many Requests
            # print('429 Too Many Requests')
            error = 'REGULAR_SUBMISSION_LIMIT'

    return success, error