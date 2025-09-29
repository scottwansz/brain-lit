import os
from urllib.parse import urlencode

from dotenv import load_dotenv

from brain_lit.logger import setup_logger
from brain_lit.svc.auth import AutoLoginSession

logger = setup_logger()

def get_dataset_list(session: AutoLoginSession, params: dict = None):
    # 获取数据
    if params is None:
        params = {
            "region": "EUR",
            "universe": "TOP2500",
            "delay": 0,
            "instrumentType": "EQUITY",
            "limit": 20,
            "offset": 0,
        }
    query_string = urlencode(params)
    url = f"https://api.worldquantbrain.com/data-sets?{query_string}"
    data_response = session.get(url)
    return data_response.json()

if __name__ == '__main__':

    logger.info("开始执行...")

    load_dotenv()
    username = os.getenv('BRAIN_USERNAME')
    password = os.getenv('BRAIN_PASSWORD')

    if not username or not password:
        logger.error("未配置环境变量 BRAIN_USERNAME 或 BRAIN_PASSWORD")
        raise ValueError("未配置环境变量 BRAIN_USERNAME 或 BRAIN_PASSWORD")

    # 根据API特性调整参数
    session = AutoLoginSession(username, password)

    # 使用自定义参数
    custom_params = {
        "region": "USA",
        "universe": "TOP3000",
        "delay": 1,
        "instrumentType": "EQUITY",
        "limit": 50,
        "offset": 0,
    }
    ds_list = get_dataset_list(session, custom_params)
    logger.info(f"数据集列表: {ds_list}")