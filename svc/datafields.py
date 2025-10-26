from svc.auth import get_auto_login_session
from svc.logger import setup_logger

url = "https://api.worldquantbrain.com/data-fields"

logger = setup_logger(__name__)

def get_fields_in_page(dataset_id='other699', delay=0, instrument_type='EQUITY', limit=20, offset=0, region='AMR', universe='TOP600'):
    """
    获取数据字段信息，返回以id为key，type为value的字典
    
    Args:
        dataset_id (str): 数据集ID
        delay (int): 延迟
        instrument_type (str): 仪器类型
        limit (int): 限制返回记录数
        offset (int): 偏移量
        region (str): 地区
        universe (str): 范围
        
    Returns:
        dict: 以id为key，type为value的字典
    """
    # 获取自动登录会话
    session = get_auto_login_session()
    
    # 设置请求参数
    params = {
        'dataset.id': dataset_id,
        'delay': delay,
        'instrumentType': instrument_type,
        'limit': limit,
        'offset': offset,
        'region': region,
        'universe': universe
    }
    
    # 发送GET请求
    response = session.get(url, params=params)
    
    # 检查响应状态
    response.raise_for_status()
    
    # 解析响应数据并构造以id为key，type为value的字典
    res_json = response.json()
    return {item['id']: {'type': item['type'], 'coverage': item['coverage']} for item in res_json.get('results', [])}


def get_single_set_fields(dataset_id='other699', delay=0, instrument_type='EQUITY', region='AMR', universe='TOP600'):
    """
    获取指定数据集的所有字段信息，返回以id为key，type为value的字典
    
    Args:
        dataset_id (str): 数据集ID
        delay (int): 延迟
        instrument_type (str): 仪器类型
        region (str): 地区
        universe (str): 范围
        
    Returns:
        dict: 以id为key，type为value的字典，包含数据集的所有字段
    """
    # 初始化结果字典
    result = {}
    
    # 分页获取所有数据
    limit = 50  # 每页获取50条记录
    offset = 0
    
    while True:
        # 调用现有的get_data_fields方法获取当前页数据
        batch_dict = get_fields_in_page(dataset_id, delay, instrument_type, limit, offset, region, universe)
        result.update(batch_dict)
        
        # 如果当前页返回的数据少于限制数量，说明已经到最后一页
        if len(batch_dict) < limit:
            break
        
        # 更新offset以获取下一页数据
        offset += limit
    
    return result


def get_multi_set_fields(dataset_ids, delay=0, instrument_type='EQUITY', region='AMR', universe='TOP600'):
    """
    获取多个数据集的所有字段信息，返回以id为key，type为value的字典
    
    Args:
        dataset_ids (list): 数据集ID列表
        delay (int): 延迟
        instrument_type (str): 仪器类型
        region (str): 地区
        universe (str): 范围
        
    Returns:
        dict: 以id为key，type为value的字典，包含所有数据集的字段
    """
    # 初始化结果字典
    result = {}
    
    # 遍历所有数据集ID，调用现有的get_all_data_fields方法
    for dataset_id in dataset_ids:
        dataset_fields = get_single_set_fields(dataset_id, delay, instrument_type, region, universe)
        result.update(dataset_fields)
    
    return result


if __name__ == "__main__":
    """
    python -c "from src.brain_lit.svc.datafields import get_all_data_fields; data = get_all_data_fields(dataset_id='analyst11'); print(data)"
    """
    # 调用函数并打印结果
    fields_dict = get_fields_in_page(dataset_id='other699')
    print(fields_dict)