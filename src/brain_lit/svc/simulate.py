import json
import threading
import time
from time import sleep
from typing import DefaultDict

import streamlit as st

from brain_lit.logger import setup_logger
from brain_lit.svc.auth import AutoLoginSession, get_auto_login_session
from brain_lit.svc.database import query_table, update_table

simulation_url = 'https://api.worldquantbrain.com/simulations'

logger = setup_logger()
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
        logger.info("Simulate_task: %s", self.simulate_tasks)
        task_id = f"{query.get('region').lower()}-delay{query.get('delay')}"

        if self.simulate_tasks.get(task_id):
            task_info = self.simulate_tasks.get(task_id)
            task_info['n_tasks_max'] = n_tasks_max
            logger.info("Simulate task %s is already running.", task_id)
        else:
            simulate_info = {
                'query': query,
                'simulate_ids': {},
                'stop': False,
                'n_tasks_max': n_tasks_max,
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
        task_id = f"{query.get('region').lower()}-delay{query.get('delay')}"
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
            'truncation': 0.08,
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

        table_name = f"{simulate_info['query']['region'].lower()}_alphas"
        records = query_table(table_name, simulate_info['query'], limit=10)
        ids = [record.get('id') for record in records]
        # logger.info('len(records): %s', len(records))
        # logger.info('records: %s', records)

        if len(records) == 0:
            logger.info("No more records to simulate.")
            simulate_info['stop'] = True
            break

        sim_data_list = []

        for record in records:
            sim_data = create_simulation_data(record)
            sim_data_list.append(sim_data)

        simulation_response = submit_simulation(session, sim_data_list)

        if simulation_response.status_code == 429:
            logger.info("Simulation failed: %s", simulation_response.content.decode())
            # Simulation failed: {"detail": "CONCURRENT_SIMULATION_LIMIT_EXCEEDED"}
            simulate_info['n_tasks_max'] = simulate_info['n_tasks_max'] - 1
            break

        if simulation_response.status_code != 201:
            logger.info("Simulation response status: %s", simulation_response.status_code)
            logger.error("Simulation failed: %s", simulation_response.content.decode())
            break

        progress_url = simulation_response.headers['Location']
        logger.info("Simulation submitted: %s", progress_url)

        simulate_id = progress_url.split('/')[-1]
        # logger.info("simulate_id: %s", simulate_id)

        update_table(table_name, {'id': ids}, {'simulated': -1, 'simulate_id': simulate_id})

        with lock:
            simulate_info['simulate_ids'][simulate_id] = {'ids': ids, 'start_time': time.time()}


def check_progress(s:AutoLoginSession, simulate_id):
    simulation_progress = s.get(f"{simulation_url}/{simulate_id}")

    # logger.info(f"{simulation_url}/{simulate_id} check_progress result: %s", simulation_progress.json())
    # {'progress': 0.15}

    if simulation_progress.headers.get("Retry-After", 0) == 0:
        return True, simulation_progress.json()

    sleep(float(simulation_progress.headers["Retry-After"]))

    # status = simulation_progress.json().get("status", 0)
    # if status != "COMPLETE":
    #     print("Not complete : %s" % (progress_url))

    # {
    #     "children": [
    #         "nldYBdEx4JUc5g1ieOcqcb",
    #         "12OKdMdcF4hf9JHlo92b1j8",
    #         "1HdNNyU253wb3r106VJgVzB",
    #         "4kFK2u66P4G6bIS1dbax9tJO",
    #         "1ZpeoDbh151DaHE9rEr9P8j",
    #         "1tvVaz3Po4ZQ8Xe5c2Tvlws",
    #         "1XFRBl7R04odaJ6mPbzcqmN",
    #         "2uBj6Jh0t5cRcnd8dICcYbf",
    #         "sgT1N20x58g9tocpayNA84",
    #         "3RVxra4e94q3cICPfdOZsPK"
    #     ],
    #     "type": "REGULAR",
    #     "settings": {
    #         "instrumentType": "EQUITY",
    #         "region": "USA",
    #         "delay": 1,
    #         "language": "FASTEXPR"
    #     },
    #     "status": "COMPLETE"
    # }

    return False, simulation_progress.json()


def check_simulate_task(session: AutoLoginSession, task_info):
    completed_simulate_ids = [simulate_id for simulate_id, simulate_info in task_info['simulate_ids'].items()
                              if simulate_info.get('end_time') is not None]

    for simulate_id in completed_simulate_ids:
        task_info['simulate_ids'].pop(simulate_id)

    with lock:
        simulate_ids_items  = list(task_info['simulate_ids'].items())

    for simulate_id, simulate_info in simulate_ids_items:
        progress_complete, response = check_progress(session, simulate_id)

        if progress_complete:
            logger.info("progress_data: %s", response)
            simulate_info.update({'end_time': time.time()})

            if response.get("status") == "COMPLETE":
                logger.info("Completed simulations: %s", simulate_id)
                save_simulate_result(session, simulate_id)
            else:
                logger.error("NOT Completed simulations: %s", simulate_id)

                table_name = f"{task_info['query']['region'].lower()}_alphas"
                ids = task_info['simulate_ids'][simulate_id]['ids']
                update_table(table_name, {'id': ids}, {'simulated': -2, 'fail_reasons': json.dumps(response)})

                for child in response.get('children', []):
                    error_url = f"{simulation_url}/{child}"
                    logger.error("Error: %s", error_url)

                    error_response = session.get(error_url).json()
                    logger.error(error_response)

        else:
            simulate_info.update(response)
            simulate_info['time_used'] = time.time() - simulate_info.get('start_time')
            logger.info("Simulate Not complete %s: %s", simulate_id, response)


def get_unsimulated_records(query, limit=10):
    """
    获取未模拟的记录
    """
    table_name = f"{query.get('region').lower()}_alphas"
    return query_table(table_name, query, limit=limit)

def save_simulate_result(s: AutoLoginSession, simulate_id):
    try:
        response = s.get(f"{simulation_url}/{simulate_id}")
    except Exception as e:
        error_message = response.content.decode('utf-8')
        logger.error("Get child of %s error: %s", simulate_id, error_message)

        # if "Incorrect authentication credentials." in error_message:
        #     s = login()

    for child in response.json().get('children', []):
        url = f"{simulation_url}/{child}"
        response = s.get(url)

        """
        response.json() example:
        {
          "id": "13SQVPgxU5fqbT735Yp8fKO",
          "parent": "3J5DmOBn5cIcK614so2AADF",
          "type": "REGULAR",
          "settings": {
            "instrumentType": "EQUITY",
            "region": "AMR",
            "universe": "TOP600",
            "delay": 0,
            "decay": 6,
            "neutralization": "SUBINDUSTRY",
            "truncation": 0.08,
            "pasteurization": "ON",
            "unitHandling": "VERIFY",
            "nanHandling": "ON",
            "maxTrade": "ON",
            "language": "FASTEXPR",
            "visualization": false
          },
          "regular": "ts_delay(winsorize(ts_backfill(anl10_ebismun_1yf_5505, 120), std=4), 240)",
          "status": "COMPLETE",
          "alpha": "E5Ze0lJR"
        }
        """

        alpha_id = response.json()['alpha']
        # regular = response.json()['regular']

        r = get_alpha_one(s, alpha_id)
        checks = r.get('is').get('checks')

        # 解析检查结果
        # passed = all(item["result"] == "PASS" for item in checks)
        fail_reasons = [check for check in checks if check.get('result') == 'FAIL']
        # print(f"Alpha {alpha_id} check passed: {passed} {fail_reasons}")

        import json

        set_data = {
            'alpha_id': r['id'],
            'sharp': r['is']['sharpe'],
            'turnover': r['is']['turnover'],
            'fitness': r['is'].get('fitness', 0),
            'passed': -1 if len(fail_reasons) > 1 else 0,
            'fail_reasons': json.dumps(fail_reasons),
            "simulated": 1,
            'simulate_id': child
        }
        where_data = {
            'alpha': r.get('regular').get('code'),
            'region': r['settings']['region'],
            'universe': r['settings']['universe'],
            'delay': r['settings']['delay'],
            'neutralization': r['settings']['neutralization']
        }

        table_name = f"{r['settings']['region'].lower()}_alphas"
        update_table(table_name, updates=set_data, conditions=where_data)



def get_alpha_one(s: AutoLoginSession, alpha_id):
    url = "https://api.worldquantbrain.com/alphas/" + alpha_id
    r = s.get(url).json()
    return r


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
            'truncation': 0.08,
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