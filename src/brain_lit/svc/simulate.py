from time import sleep

from brain_lit.svc.auth import AutoLoginSession


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
        'regular': r.get('alpha')}
    return simulation_data


def submit_simulation(s:AutoLoginSession, sim_data_list: list = None):
    simulation_response = s.post('https://api.worldquantbrain.com/simulations', json=sim_data_list)
    return simulation_response


def check_progress(s:AutoLoginSession, simulate_id):
    simulation_progress = s.get(f'https://api.worldquantbrain.com/simulations/{simulate_id}')

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