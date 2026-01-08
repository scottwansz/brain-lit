import json
import threading
import time
from json import JSONDecodeError
from time import sleep
from typing import DefaultDict

import streamlit as st

from svc.auth import get_auto_login_session, AutoLoginSession
from svc.database import query_table, update_table
from svc.logger import setup_logger

simulation_url = 'https://api.worldquantbrain.com/simulations'

logger = setup_logger(__name__)
lock = threading.Lock()

@st.cache_resource
def get_simulate_task_manager():
    return SimulateTaskManager()


class SimulateTaskManager:
    def __init__(self):
        self.session = get_auto_login_session()
        self.simulate_submit_thread = None
        self.simulate_check_thread = None
        self.simulate_tasks = DefaultDict(dict)
        self._lock = threading.Lock()

    def start_simulate(self, query, n_tasks_max=10):
        logger.info("Simulate_query: %s", query)
        task_id = f"{query.get('region')}-delay{query.get('delay')}"

        if self.simulate_tasks.get(task_id):
            task_info = self.simulate_tasks.get(task_id)
            task_info.update({
                "query": query,
                "stop": False,
                "n_tasks_max": n_tasks_max,
                "n_tasks": len(task_info['simulate_ids']),
            })
            logger.info("Simulate task %s is already running.", task_id)
        else:
            simulate_info = {
                'query': query,
                'stop': False,
                'n_tasks_max': n_tasks_max,
                'n_tasks': 0,
                'simulate_ids': {},
            }
            self.simulate_tasks[task_id] = simulate_info
            logger.info("Simulate task %s is started.", task_id)

        if self.simulate_submit_thread is None:
            self.simulate_submit_thread = threading.Thread(target=self.start_auto_submit, daemon=True)
            self.simulate_submit_thread.start()
            logger.info("Simulate SUBMIT is started.")
        else:
            logger.info("Simulate SUBMIT is already running.")

        if self.simulate_check_thread is None:
            self.simulate_check_thread = threading.Thread(target=self.start_monitoring, daemon=True)
            self.simulate_check_thread.start()
            logger.info("Simulate CHECK is started.")
        else:
            logger.info("Simulate CHECK is already running.")

    def stop_simulate(self, query):
        task_id = f"{query.get('region')}-delay{query.get('delay')}"
        task_info = self.simulate_tasks.get(task_id)
        if task_info:
            task_info['stop'] = True
            logger.info(f"Simulate task {task_id} is stopped.")
        else:
            logger.info(f"Simulate task {task_id} is not running.")

    def start_auto_submit(self):
        # 提交回测任务
        while True:

            time.sleep(0.5)

            # completed_task_ids = [task_id for task_id, task_info in self.simulate_tasks.items() if len(task_info['simulate_ids']) == 0 and task_info['stop']]

            # for task_id in completed_task_ids:
            #     self.simulate_tasks.pop(task_id)

            with self._lock:
                todo_task_infos = [task_info for task_id, task_info in self.simulate_tasks.items() if not task_info['stop']]

            if len(todo_task_infos) == 0:
                self.simulate_submit_thread = None
                logger.info("Simulate SUBMIT is stopped.")
                break

            for task_info in todo_task_infos:
                submit_simulation_task(self.session, task_info)

    def start_monitoring(self):
        # 检测回测任务执行状态
        while True:

            time.sleep(1)

            with self._lock:
                completed_task_ids = [task_id for task_id, task_info in self.simulate_tasks.items() if len(task_info['simulate_ids']) == 0 and task_info['stop']]
                # logger.info("completed_task_ids: %s", completed_task_ids)

                for task_id in completed_task_ids:
                    self.simulate_tasks.pop(task_id)

                todo_task_infos = [task_info for task_id, task_info in self.simulate_tasks.items()]

            if len(todo_task_infos) == 0:
                self.simulate_check_thread = None
                logger.info("Simulate CHECK is stopped.")
                break

            for task_info in todo_task_infos:
                check_simulate_task(self.session, task_info)


def create_simulation_data(r: dict):
    simulation_data = {
        'type': 'REGULAR',
        'settings': {
            'instrumentType': 'EQUITY',
            'region': r.get('region'),
            'universe': r.get('universe'),
            'delay': r.get('delay'),
            'decay': r.get('decay'),
            'neutralization': r.get('neutralization'),
            'truncation': 0.01,
            'pasteurization': 'ON',
            'testPeriod': 'P2Y',
            'unitHandling': 'VERIFY',
            'nanHandling': 'ON',
            'language': 'FASTEXPR',
            'visualization': False,
            'maxTrade': 'ON',
        },
        'regular': r.get('alpha')
    }
    return simulation_data


def submit_simulation(s:AutoLoginSession, sim_data_list: list = None):
    simulation_response = s.post(simulation_url, json=sim_data_list)
    return simulation_response


def submit_simulation_task(session: AutoLoginSession, simulate_info):
    while len(simulate_info['simulate_ids']) < simulate_info['n_tasks_max'] and not simulate_info['stop']:

        table_name = f"{simulate_info['query']['region'].lower()}_alphas" if simulate_info['query']['region'] else 'all_alphas'
        records = query_table(table_name, simulate_info['query'], limit=10)
        ids = [record.get('id') for record in records]
        # logger.info('len(records): %s', len(records))
        # logger.info('records: %s', records)

        if len(records) == 0:
            logger.info("No more records to simulate.")
            simulate_info['stop'] = True
            break

        sim_data_list = []
        first_region = records[0].get('region')

        for record in records:

            if record.get('region') != first_region or len(sim_data_list)==10:
                submit_one_batch(ids, session, sim_data_list, simulate_info, table_name)
                sim_data_list = []
                first_region = record.get('region')

            sim_data = create_simulation_data(record)
            sim_data_list.append(sim_data)

        submit_one_batch(ids, session, sim_data_list, simulate_info, table_name)


def submit_one_batch(ids, session, sim_data_list, simulate_info, table_name):
    simulation_response = submit_simulation(session, sim_data_list if len(sim_data_list) > 1 else sim_data_list[0])
    if simulation_response.status_code == 429:
        logger.warning("Simulate FAILED: %s", simulation_response.content.decode())
        # Simulation failed: {"detail": "CONCURRENT_SIMULATION_LIMIT_EXCEEDED"}
        simulate_info['n_tasks_max'] = simulate_info['n_tasks_max'] - 1
        return
    if simulation_response.status_code != 201:
        logger.error("Simulation response status: %s", simulation_response.status_code)
        logger.error("Simulation failed: %s", simulation_response.content.decode())
        # print(json.dumps(sim_data_list, indent=4, ensure_ascii=False))
        return
    progress_url = simulation_response.headers['Location']
    logger.info("Simulate SUBMITTED: %s", progress_url)
    simulate_id = progress_url.split('/')[-1]
    # logger.info("simulate_id: %s", simulate_id)
    update_table(table_name, {'id': ids}, {'simulated': -1, 'simulate_id': simulate_id})
    with lock:
        simulate_info['simulate_ids'][simulate_id] = {'ids': ids, 'start_time': time.time()}
        simulate_info['n_tasks'] = len(simulate_info['simulate_ids'])


def check_progress(s:AutoLoginSession, simulate_id):
    simulation_progress = s.get(f"{simulation_url}/{simulate_id}")

    # logger.info(f"{simulation_url}/{simulate_id} check_progress result: %s", simulation_progress.json())
    # {'progress': 0.15}

    if simulation_progress.status_code == 504:
        logger.warning("Simulate 504 FAILED: %s", simulation_progress.content.decode())
        # 504 Gateway Time - out
        return False, {'errr': '504 Gateway Time - out'}
    
    # 添加响应检查
    if not simulation_progress.ok:
        logger.error("Failed to check progress for %s. Status code: %s", simulate_id, simulation_progress.status_code)
        logger.error("Response content: %s", simulation_progress.content.decode('utf-8') if simulation_progress.content else "Empty response")
        return True, {}

    if simulation_progress.headers.get("Retry-After", 0) == 0:
        # 检查响应内容是否可以解析为JSON
        try:
            response_json = simulation_progress.json()
            return True, response_json
        except json.JSONDecodeError as e:
            logger.error("Failed to decode JSON for progress check %s. Error: %s", simulate_id, str(e))
            logger.error("Response content: %s", simulation_progress.content.decode('utf-8') if simulation_progress.content else "Empty response")
            return True, {}

    sleep(float(simulation_progress.headers["Retry-After"]))

    # 检查响应内容是否可以解析为JSON
    try:
        response_json = simulation_progress.json()
        return False, response_json
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON for progress check %s. Error: %s", simulate_id, str(e))
        logger.error("Response content: %s", simulation_progress.content.decode('utf-8') if simulation_progress.content else "Empty response")
        return False, {}


def check_simulate_task(session: AutoLoginSession, task_info):
    table_name = f"{task_info['query']['region'].lower()}_alphas" if task_info['query']['region'] else 'all_alphas'
    completed_simulate_ids = [simulate_id for simulate_id, simulate_info in task_info['simulate_ids'].items()
                              if simulate_info.get('end_time') is not None]

    for simulate_id in completed_simulate_ids:
        task_info['simulate_ids'].pop(simulate_id)
        task_info['n_tasks'] = len(task_info['simulate_ids'])

    with lock:
        simulate_ids_items  = list(task_info['simulate_ids'].items())

    for simulate_id, simulate_info in simulate_ids_items:
        progress_complete, response = check_progress(session, simulate_id)

        if progress_complete:
            # logger.info("progress_data: %s", response)
            simulate_info.update({'end_time': time.time()})

            if response.get("status") in ["COMPLETE", "WARNING"]:
                time_used = time.time() - simulate_info.get('start_time')
                logger.info("Completed simulations in %s seconds: %s", int(time_used), simulate_id)
                if response.get("alpha"):
                    save_alpha_simulate_result(response.get('alpha'), simulate_id, session, table_name)
                else:
                    save_simulate_result(session, simulate_id, table_name=table_name)
            else:
                logger.error("Fail simulations: %s", simulate_id)
                logger.error("Fail reasons: \n%s", json.dumps(response, indent=4, ensure_ascii=False))

                ids = task_info['simulate_ids'][simulate_id]['ids']
                update_table(table_name, {'id': ids}, {'simulated': -2, 'fail_reasons': json.dumps(response)})

                for child in response.get('children', []):
                    error_url = f"{simulation_url}/{child}"
                    logger.error("Error: %s", error_url)

                    error_response = session.get(error_url)
                    logger.error("Error response: %s", error_response.status_code)
                    logger.error("Error response content: %s", error_response.content.decode('utf-8') if error_response.content else "Empty response")

        else:
            simulate_info.update(response)
            time_used = time.time() - simulate_info.get('start_time')
            simulate_info['time_used'] = time_used

            if time_used > 3600:
                simulate_info.update({'end_time': time.time(), 'error': 'timeout'})
                logger.warning("Simulate timeout: %s", simulate_id)

            logger.info("Simulate IN PROGRESS %s: %s", simulate_id, response)


def get_unsimulated_records(query, limit=10):
    """
    获取未模拟的记录
    """
    table_name = f"{query.get('region').lower()}_alphas" if query.get('region') else "all_alphas"
    return query_table(table_name, query, limit=limit)


def save_simulate_result(s: AutoLoginSession, simulate_id, table_name=None):
    try:
        response = s.get(f"{simulation_url}/{simulate_id}")
    except Exception as e:
        error_message = response.content.decode('utf-8')
        logger.error("Get simulate %s error: %s", simulate_id, error_message)

        # if "Incorrect authentication credentials." in error_message:
        #     s = login()

    # 添加检查响应是否成功
    if not response.ok:
        logger.error("Failed to get simulation result for %s. Status code: %s", simulate_id, response.status_code)
        logger.error("Response content: %s", response.content.decode('utf-8') if response.content else "Empty response")
        return

    # 检查响应内容是否为空
    if not response.content:
        logger.error("Empty response received for simulation %s", simulate_id)
        return

    try:
        response_json = response.json()
    except JSONDecodeError as e:
        logger.error("Failed to decode JSON for simulation %s. Error: %s", simulate_id, str(e))
        logger.error("Response content: %s", response.content.decode('utf-8') if response.content else "Empty response")
        return

    if response_json.get('alpha'):
        save_alpha_simulate_result(response_json.get('alpha'), simulate_id, s, table_name)
        return

    for child in response_json.get('children', []):
        url = f"{simulation_url}/{child}"
        response = s.get(url)

        try_count = 0
        while response.status_code == 504 and try_count < 5:
            try_count += 1
            logger.warning("504 Gateway Timeout for CHILD simulation %s. Retrying... %s", simulate_id, try_count)
            sleep(5)
            response = s.get(url)

        # 检查子任务响应
        if not response.ok:
            logger.error("Failed to get CHILD simulation %s. Status code: %s", child, response.status_code)
            logger.error("Response content: %s", response.content.decode('utf-8') if response.content else "Empty response")
            continue

        if not response.content:
            logger.error("Empty response received for CHILD simulation %s", child)
            continue

        try:
            child_response_json = response.json()
        except json.JSONDecodeError as e:
            logger.error("Failed to decode JSON for CHILD simulation %s. Error: %s", child, str(e))
            logger.error("Response content: %s", response.content.decode('utf-8') if response.content else "Empty response")
            continue

        # 检查响应中是否包含 'alpha' 字段
        if 'alpha' not in child_response_json:
            logger.error("Missing 'alpha' field in response for child simulation %s", child)
            logger.error("Response content: %s", json.dumps(child_response_json, indent=2))
            continue

        alpha_id = child_response_json['alpha']
        # regular = response.json()['regular']

        save_alpha_simulate_result(alpha_id, child, s, table_name)


def save_alpha_simulate_result(alpha_id, simulate_id, s, table_name):
    r = get_alpha_one(s, alpha_id)
    if not r:
        logger.error("Failed to get alpha simulate result: %s", alpha_id)
        return
    checks = r.get('is').get('checks')
    # 解析检查结果
    # passed = all(item["result"] == "PASS" for item in checks)
    fail_reasons = [check for check in checks if check.get('result') == 'FAIL']
    # print(f"Alpha {alpha_id} check passed: {passed} {fail_reasons}")
    import json
    if r['is']['shortCount'] + r['is']['longCount'] < 100 or r['train']['shortCount'] + r['train']['longCount'] < 100 or r['test']['shortCount'] + r['test']['longCount'] < 100:
        passed = -3
        fail_reasons = [{'name': 'NOT_ENOUGH_TRADES', 'result': 'FAIL'}]
    elif len(fail_reasons) > 1:
        passed = -1
    else:
        passed = 0
    set_data = {
        'alpha_id': r['id'],
        'sharp': r['is']['sharpe'],
        'turnover': r['is']['turnover'],
        'fitness': r['is'].get('fitness', 0),
        'is_long': r['is']['longCount'],
        'is_short': r['is']['shortCount'],
        'train_long': r['train']['longCount'],
        'train_short': r['train']['shortCount'],
        'test_long': r['test']['longCount'],
        'test_short': r['test']['shortCount'],
        'passed': passed,
        'fail_reasons': json.dumps(fail_reasons),
        "simulated": 1,
        'simulate_id': simulate_id
    }
    where_data = {
        'alpha': r.get('regular').get('code'),
        'region': r['settings']['region'],
        'universe': r['settings']['universe'],
        'delay': r['settings']['delay'],
        'neutralization': r['settings']['neutralization']
    }
    # table_name = f"{r['settings']['region'].lower()}_alphas"
    update_table(table_name, updates=set_data, conditions=where_data)

def get_long_short_count_from_yearly_stats(alpha_id):
    url = f"https://api.worldquantbrain.com/alphas/{alpha_id}/recordsets/yearly-stats"
    s = get_auto_login_session()
    records = s.get(url).json().get('records')
    long_count, short_count = 0, 0
    for record in records:
        long_count += int(record[9])
        short_count += int(record[10])
    return long_count + short_count


def get_alpha_one(s: AutoLoginSession, alpha_id, retry=0):
    url = f"https://api.worldquantbrain.com/alphas/{alpha_id}"
    response = s.get(url)

    if response.status_code == 504:
        logger.warning("Timeout error when getting alpha %s, retried %s", alpha_id, retry)
        if retry > 3:
            logger.error("Timeout error when getting alpha %s, retried %s", alpha_id, retry)
            return {}
        return get_alpha_one(s, alpha_id, retry + 1)
    
    # 添加响应检查
    if not response.ok:
        logger.error("Failed to get alpha %s. Status code: %s", alpha_id, response.status_code)
        logger.error("Response content: %s", response.content.decode('utf-8') if response.content else "Empty response")
        return {}
    
    if not response.content:
        logger.error("Empty response received for alpha %s", alpha_id)
        return {}

    try:
        r = response.json()
        return r
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON for alpha %s. Error: %s", alpha_id, str(e))
        logger.error("Response content: %s", response.content.decode('utf-8') if response.content else "Empty response")
        return {}


def single_alpha_tune(s:AutoLoginSession, alpha: str, region: str = 'USA', delay: int = 1, universe: str = 'TOP3000'):
    neutralization_array = [
        "NONE",
        "STATISTICAL",
        "CROWDING",
        "FAST",
        "SLOW",
        "MARKET",
        "SECTOR",
        "INDUSTRY",
        # "SUBINDUSTRY",
        "SLOW_AND_FAST",
        "STATISTICAL",
        # "COUNTRY"
    ]
    sim_data_list = [{
        'type': 'REGULAR',
        'settings': {
            'instrumentType': 'EQUITY',
            'region': region,
            'universe': universe,
            'delay': delay,
            'decay': 6,
            'neutralization': n,
            'truncation': 0.01,
            'pasteurization': 'ON',
            'testPeriod': 'P2Y',
            'unitHandling': 'VERIFY',
            'nanHandling': 'ON',
            'language': 'FASTEXPR',
            'visualization': False,
            'maxTrade': 'ON',
        },
        'regular': alpha
    } for n in neutralization_array]

    print(sim_data_list)

    simulation_response = submit_simulation(s, sim_data_list)
    error_message = simulation_response.content.decode('utf-8')

    if error_message:
        print("loc key error: %s" % error_message)
    else:
        url = simulation_response.headers['Location']
        print("submitted:", url)

        while True:
            completed, response = check_progress(s, url)
            print("Progress:", response.get("progress"))

            if completed:

                if response.get("status") == "COMPLETE":
                    print("Completed:", url)
                else:
                    print("Failed:", url)

                break