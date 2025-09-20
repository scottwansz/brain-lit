from urllib.parse import urlencode

from brain_lit.logger import setup_logger
from brain_lit.svc.auth import AutoLoginSession

logger = setup_logger()

def get_dateset_list(session: AutoLoginSession, params: dict = None):
    # 获取数据
    if params is None:
        params = {
            "delay": 0,
            "instrumentType": "EQUITY",
            "limit": 20,
            "offset": 0,
            "region": "EUR",
            "universe": "TOP2500"
        }
    query_string = urlencode(params)
    url = f"https://api.worldquantbrain.com/data-sets?{query_string}"
    data_response = session.get(url)
    return data_response.json()

if __name__ == '__main__':

    logger.info("开始执行...")

    # 根据API特性调整参数
    session = AutoLoginSession()

    # 使用自定义参数
    custom_params = {
        "region": "USA",
        "universe": "TOP3000",
        "delay": 1,
        "instrumentType": "EQUITY",
        "limit": 50,
        "offset": 0,
    }
    ds_list = get_dateset_list(session, custom_params)
    logger.info(f"数据集列表: {ds_list}")