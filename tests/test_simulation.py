import time
import unittest
from typing import DefaultDict

from brain_lit.svc.auth import AutoLoginSession
from brain_lit.svc.database import query_table, update_table
from brain_lit.svc.simulate import get_unsimulated_records, create_simulation_data, submit_simulation, check_progress, \
    save_simulate_result


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
                "truncation": 0.08,
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

        simulate_tasks = DefaultDict(dict)
        n_tasks = 2

        # 提交回测任务
        while True:
            if len(simulate_tasks) < n_tasks:

                table_name = f"{query.get('region').lower()}_alphas"
                records = query_table(table_name, query, limit=2)

                if len(records) == 0:
                    print("No more records to simulate.")
                    break

                ids = [record.get('id') for record in records]
                print(len(records))
                print(records)

                sim_data_list = []

                for record in records:
                    sim_data = create_simulation_data(record)
                    sim_data_list.append(sim_data)

                simulation_response = submit_simulation(session, sim_data_list)
                progress_url = simulation_response.headers['Location']
                print("Simulation submitted:", progress_url)

                update_table(table_name, {'id': ids}, {'simulated': -1})

                simulate_id = progress_url.split('/')[-1]
                print("simulate_id:", simulate_id)

                simulate_tasks[simulate_id] = {'ids': ids, 'start_time': time.time()}

        # 检测回测任务执行状态
        while True:
            for simulate_id, task_info in simulate_tasks.items():
                progress_complete, response = check_progress(session, simulate_id)

                if progress_complete:
                    print("progress_data:", response)
                    simulate_tasks.pop(simulate_id)

                    if response.get("status") == "COMPLETE":
                        print("Completed simulations:", simulate_id)
                        save_simulate_result(session, simulate_id)
                    else:
                        print("NOT Completed simulations:", simulate_id)

                        for child in response.get('children', []):
                            error_url = "https://api.worldquantbrain.com/simulations/" + child
                            print("Error:", error_url)
                            print(session.get(error_url).json())

                        update_table(table_name, {'id': ids}, {'simulated': -2})

            time.sleep(1)
