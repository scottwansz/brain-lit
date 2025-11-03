from urllib.parse import urlencode

import streamlit as st

from svc.auth import get_auto_login_session
from svc.database import get_db_connection
from svc.logger import setup_logger

logger = setup_logger(__name__)

def get_dataset_list(params: dict = None):
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
    session = get_auto_login_session()
    data_response = session.get(url)
    return data_response.json()


@st.cache_data(ttl=3600*24)
def get_all_datasets(params: dict = None):
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
    
    first_page_response = get_dataset_list(first_page_params)
    
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
            
            page_response = get_dataset_list(page_params)
            # 检查返回的数据格式
            if isinstance(page_response, dict):
                page_datasets = page_response.get("results", [])
            else:
                page_datasets = page_response if isinstance(page_response, list) else []
                
            if isinstance(page_datasets, list):
                all_datasets.extend(page_datasets)
    
    return all_datasets # , total_count

# @st.cache_data(ttl=3600)
def get_used_dataset_ids(region: str, universe: str, delay: int, template: str) -> set:
    """
    从数据库获取已使用的数据集ID集合
    
    Args:
        region:     区域参数
        universe:   范围参数
        delay:      延迟参数
        template:   表达式模板
        
    Returns:
        已使用的数据集ID集合
    """
    try:
        connection = get_db_connection()
        if not connection:
            return set()
        
        cursor = connection.cursor()
        
        # 查询已使用的数据集
        query = """
        SELECT dataset FROM dataset_used 
        WHERE region = %s AND universe = %s AND delay = %s AND template = %s
        """
        cursor.execute(query, (region, universe, delay, template))
        
        # 获取结果
        used_dataset_ids = set()
        for (dataset_id,) in cursor.fetchall():
            used_dataset_ids.add(dataset_id)
        
        cursor.close()
        connection.close()
        
        return used_dataset_ids
    except Exception as e:
        print(f"查询已使用的数据集时出错: {e}")
        return set()