from svc.auth import get_auto_login_session
from svc.logger import setup_logger

url = "https://api.worldquantbrain.com/data-fields"

logger = setup_logger(__name__)

def get_data_fields(dataset_id='other699', delay=0, instrument_type='EQUITY', limit=20, offset=0, region='AMR', universe='TOP600'):
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


def get_all_data_fields(dataset_id='other699', delay=0, instrument_type='EQUITY', region='AMR', universe='TOP600'):
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
    # 获取自动登录会话
    session = get_auto_login_session()
    
    # 初始化结果字典
    result = {}
    
    # 分页获取所有数据
    limit = 50  # 每页获取20条记录（与API默认限制一致）
    offset = 0
    
    while True:
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
        
        # 解析响应数据
        res_json = response.json()
        
        # 将当前页的数据添加到结果字典中
        batch_dict = {item['id']: {'type': item['type'], 'coverage': item['coverage']} for item in res_json.get('results', [])}
        result.update(batch_dict)
        
        # 检查是否还有更多数据
        if len(res_json.get('results', [])) < limit:
            # 如果当前页返回的数据少于限制数量，说明已经到最后一页
            break
        
        # 更新offset以获取下一页数据
        offset += limit
    
    return result


if __name__ == "__main__":
    """
    python -c "from src.brain_lit.svc.datafields import get_all_data_fields; data = get_all_data_fields(dataset_id='analyst11'); print(data)"
    """
    # 调用函数并打印结果
    fields_dict = get_data_fields(dataset_id='other699')
    print(fields_dict)