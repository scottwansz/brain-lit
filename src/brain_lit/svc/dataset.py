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

def get_all_datasets(session: AutoLoginSession, params: dict = None):
    """
    获取所有数据集，不分页
    """
    if params is None:
        params = {
            "region": "EUR",
            "universe": "TOP2500",
            "delay": 0,
            "instrumentType": "EQUITY",
        }
    
    # 移除limit和offset参数，获取所有数据
    params_without_pagination = params.copy()
    params_without_pagination.pop("limit", None)
    params_without_pagination.pop("offset", None)
    
    # 先获取第一页以确定总数
    first_page_params = params_without_pagination.copy()
    first_page_params["limit"] = 50
    first_page_params["offset"] = 0
    
    first_page_response = get_dataset_list(session, first_page_params)
    
    # 检查返回的数据格式
    if isinstance(first_page_response, dict):
        all_datasets = first_page_response.get("results", [])
        total_count = first_page_response.get("count", len(all_datasets))
    else:
        # 如果直接返回列表
        all_datasets = first_page_response if isinstance(first_page_response, list) else []
        total_count = len(all_datasets)
    
    # 如果总数量大于当前获取的数量，继续获取剩余数据
    page_size = 50
    if total_count > len(all_datasets):
        # 计算需要获取的页数
        total_pages = (total_count + page_size - 1) // page_size
        
        # 获取剩余页面的数据
        for page in range(1, total_pages):
            page_params = params_without_pagination.copy()
            page_params["limit"] = page_size
            page_params["offset"] = page * page_size
            
            page_response = get_dataset_list(session, page_params)
            # 检查返回的数据格式
            if isinstance(page_response, dict):
                page_datasets = page_response.get("results", [])
            else:
                page_datasets = page_response if isinstance(page_response, list) else []
                
            if isinstance(page_datasets, list):
                all_datasets.extend(page_datasets)
    
    return all_datasets, total_count

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

    dataset_all = get_all_datasets(session, custom_params)
    logger.info(f"所有数据集: {dataset_all}")