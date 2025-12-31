import time
import unittest
from typing import DefaultDict

from svc.auth import AutoLoginSession
from svc.logger import setup_logger
from svc.simulate import get_unsimulated_records, check_progress, \
    submit_simulation_task, check_simulate_task

logger = setup_logger(__name__)

class TestMain(unittest.TestCase):
    def test_main(self):
        # 添加测试代码
        self.assertEqual(1, 1)

    def test_get_unsimulated_records(self):
        query = {
            'region': 'JPN',
            'universe': 'TOP1600',
            'delay': 0,
            'simulated': 0,
        }

        records = get_unsimulated_records(query, limit=10)
        print(len(records))
        print(records)
        self.assertEqual(1, 1)


    def test_simulate(self):
        import streamlit as st
        username = st.secrets["brain"]["username"]
        password = st.secrets["brain"]["password"]
        session = AutoLoginSession(username, password)

        simulation_data = {
            # 'my_id': '123',
            'type': 'REGULAR',
            "settings": {
                "instrumentType": "EQUITY",
                "region": "AMR",
                "universe": "TOP600",
                "delay": 0,
                "decay": 6,
                "neutralization": "SUBINDUSTRY",
                "truncation": 0.01,
                "pasteurization": "ON",
                "unitHandling": "VERIFY",
                "nanHandling": "ON",
                "maxTrade": "ON",
                "language": "FASTEXPR",
                "visualization": False
            },
            "regular": "ts_delay(winsorize(ts_backfill(anl10_ebismun_1yf_5505, 120), std=4), 240)",
        }

        simulation_response = session.post('https://api.worldquantbrain.com/simulations', json=simulation_data)
        print("Simulation submitted:", simulation_response.status_code)
        print("Simulation submitted:", simulation_response.content)
        # Simulation submitted: 201
        # Simulation submitted: b''
        # Simulation submitted: 400
        # Simulation submitted: b'{"myId":["Unexpected property."]}'
        # Simulation submitted: 400
        # Simulation submitted: b'{"settings":{"region":["\\"AMR1\\" is not a valid choice."]}}'

        progress_url = simulation_response.headers['Location']
        print("Simulation submitted:", progress_url)

        simulate_id = progress_url.split('/')[-1]
        print("simulate_id:", simulate_id)

        while True:
            progress_complete, response = check_progress(session, simulate_id)
            print("Progress:", response)

            if progress_complete:
                print("progress_data:", response)

                if response.get("status") == "COMPLETE":
                    print("Completed simulations:", simulate_id)

                else:
                    print("NOT Completed simulations:", simulate_id)

                    for child in response.get('children', []):
                        error_url = "https://api.worldquantbrain.com/simulations/" + child
                        print("Error:", error_url)
                        print(session.get(error_url).json())

                break

            time.sleep(1)


    def test_batch_simulate(self):
        import streamlit as st
        username = st.secrets["brain"]["username"]
        password = st.secrets["brain"]["password"]
        session = AutoLoginSession(username, password)

        query = {
            'region': 'JPN',
            'universe': 'TOP1600',
            'delay': 0,
            'simulated': 0,
        }
        task_id = f"{query.get('region').lower()}-delay{query.get('delay')}"
        n_tasks_max = 2

        simulate_tasks = DefaultDict(dict)
        simulate_tasks[task_id] = {
            'n_tasks_max': n_tasks_max,
            'query': query,
            'start_time': time.strftime("%Y-%m-%d %H:%M:%S"),
            'simulate_ids': {},
            'stop': False,
        }

        # 提交回测任务
        while True:
            for task_id, task_info in simulate_tasks.items():

                if len(task_info['simulate_ids']) == 0 and task_info['stop']:
                    simulate_tasks.pop(task_id)
                    continue

                submit_simulation_task(session, task_info)

        # 检测回测任务执行状态
        while True:
            if len(simulate_tasks) == 0:
                break

            for task_id, task_info in simulate_tasks.items():

                if len(task_info['simulate_ids']) == 0 and task_info['stop']:
                    simulate_tasks.pop(task_id)
                    continue

                check_simulate_task(session, task_info)
