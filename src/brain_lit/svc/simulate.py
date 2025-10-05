import os
from time import sleep
from typing import DefaultDict

from brain_lit.logger import setup_logger
from brain_lit.svc.auth import AutoLoginSession
from brain_lit.svc.database import query_table, update_table

simulation_url = 'https://api.worldquantbrain.com/simulations/'

logger = setup_logger()


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


def check_progress(s:AutoLoginSession, simulate_id):
    simulation_progress = s.get(simulation_url + simulate_id)

    # print(progress_url, simulation_progress.json())
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


def get_unsimulated_records(query, limit=10):
    """
    获取未模拟的记录
    """
    table_name = f"{query.get('region').lower()}_alphas"
    return query_table(table_name, query, limit=limit)

def save_simulate_result(s: AutoLoginSession, simulate_id):
    try:
        response = s.get(simulation_url.format(simulate_id))
    except Exception as e:
        error_message = response.content.decode('utf-8')
        print("save_simulate_result error: %s" % error_message)

        # if "Incorrect authentication credentials." in error_message:
        #     s = login()

    for child in response.json().get('children', []):
        url = simulation_url + child
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
            "simulated": 1
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


if __name__ == '__main__':
    # 加载.env文件
    from dotenv import load_dotenv
    load_dotenv()

    username = os.getenv('BRAIN_USERNAME')
    password = os.getenv('BRAIN_PASSWORD')

    if not username or not password:
        logger.error("未配置环境变量 BRAIN_USERNAME 或 BRAIN_PASSWORD")
        exit(1)

    session = AutoLoginSession()
    session.login_with_credentials(username, password)

    simulate_tasks = DefaultDict(dict)
    n_tasks = 3

    query = {
        'region': 'JPN',
        'universe': 'TOP1600',
        'delay': 0,
        'simulated': None,
    }

    records = get_unsimulated_records(query, limit=10)

    sim_data_list = []
    for record in records:
        sim_data = create_simulation_data(record)
        sim_data_list.append(sim_data)
        simulation_response = submit_simulation(session, sim_data_list)