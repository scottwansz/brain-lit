from typing import List, Dict, Any

from svc.database import get_db_connection
from svc.logger import setup_logger

logger = setup_logger(__name__)

def query_alphas_by_dataset(region: str = None, universe: str = None, delay: int = None, dataset: str = None) -> List[Dict[str, Any]]:
    """
    根据数据集查询Alpha记录
    
    Args:
        region: 地区 (USA, EUR, ASI, CHN, GLB), None表示查询所有地区
        universe: 范围, None表示查询所有universe
        delay: 延迟, None表示查询所有delay
        dataset: 数据集ID
        
    Returns:
        匹配的Alpha记录列表
    """
    # 根据地区确定表名，如果region为None，则使用all_alphas表
    if region is None:
        table_name = "all_alphas"
    else:
        table_name = f"{region.lower()}_alphas"
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # 构建查询语句和参数
        query = f"""
        SELECT id, alpha, sharp, fitness, decay, neutralization, phase, created_at, updated_at 
        FROM {table_name} 
        WHERE 1=1
        """
        params = []
        
        # 根据参数是否为None来决定是否添加查询条件
        if universe is not None:
            query += " AND universe = %s"
            params.append(universe)
        if delay is not None:
            query += " AND delay = %s"
            params.append(delay)
        if dataset is not None:
            query += " AND dataset = %s"
            params.append(dataset)
        
        query += " ORDER BY sharp*fitness DESC LIMIT 100"
        
        cursor.execute(query, params)
        
        # 获取结果
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
    except Exception as e:
        print(f"查询Alpha记录时出错: {e}")
        return []


def query_alphas_by_conditions(region: str = None, universe: str = None, delay: int = None, category: str = None, dataset_ids: List[str] = None) -> List[Dict[str, Any]]:
    """
    根据查询条件查询Alpha记录
    
    Args:
        region: 地区 (USA, EUR, ASI, CHN, GLB), None表示查询所有地区
        universe: 范围, None表示查询所有universe
        delay: 延迟, None表示查询所有delay
        category: 分类（可选）
        dataset_ids: 数据集ID列表（可选）
        
    Returns:
        匹配的Alpha记录列表
    """
    # 根据地区确定表名，如果region为None，则使用all_alphas表
    if region is None:
        table_name = "all_alphas"
    else:
        table_name = f"{region.lower()}_alphas"
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # 构建查询语句
        query = f"""
        SELECT * 
        FROM {table_name} 
        WHERE 1=1
        """
        params = []
        
        # 根据参数是否为None来决定是否添加查询条件
        if universe is not None:
            query += " AND universe = %s"
            params.append(universe)
        if delay is not None:
            query += " AND delay = %s"
            params.append(delay)
        
        # 如果指定了分类，添加分类条件
        if category and category != "All":
            query += " AND category = %s"
            params.append(category.lower())
        
        # 如果指定了数据集ID列表，添加数据集条件
        if dataset_ids:
            placeholders = ','.join(['%s'] * len(dataset_ids))
            query += f" AND dataset IN ({placeholders})"
            params.extend(dataset_ids)
        
        query += " ORDER BY sharp*fitness DESC LIMIT 500"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
    except Exception as e:
        print(f"根据条件查询Alpha记录时出错: {e}")
        return []


def query_alphas_simulation_stats(region: str = None, universe: str = None, delay: int = None, category: str = None, dataset_ids: List[str] = None, phase: int = 1) -> List[Dict[str, Any]]:
    """
    按simulated值和category进行汇总统计
    
    Args:
        region: 地区 (USA, EUR, ASI, CHN, GLB), None表示查询所有地区
        universe: 范围, None表示查询所有universe
        delay: 延迟, None表示查询所有delay
        category: 分类（可选）
        dataset_ids: 数据集ID列表（可选）
        phase: 回测阶段
        
    Returns:
        按simulated值和category分组的统计结果
    """
    # 根据地区确定表名，如果region为None，则使用all_alphas表
    if region is None:
        table_name = "all_alphas"
    else:
        table_name = f"{region.lower()}_alphas"
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # 构建统计查询语句
        query = f"""
        SELECT category, simulated, COUNT(*) as count
        FROM {table_name} 
        WHERE 1=1
        """
        params = []
        
        # 根据参数是否为None来决定是否添加查询条件
        if universe is not None:
            query += " AND universe = %s"
            params.append(universe)
        if delay is not None:
            query += " AND delay = %s"
            params.append(delay)
        
        # phase参数默认值为1，所以如果为None则不添加条件
        if phase is not None:
            query += " AND phase = %s"
            params.append(phase)
        
        # 如果指定了分类，添加分类条件
        if category and category != "All":
            query += " AND category = %s"
            params.append(category.lower())
        
        # 如果指定了数据集ID列表，添加数据集条件
        if dataset_ids:
            placeholders = ','.join(['%s'] * len(dataset_ids))
            query += f" AND dataset IN ({placeholders})"
            params.extend(dataset_ids)
        
        query += " GROUP BY category, simulated ORDER BY category, simulated"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
    except Exception as e:
        print(f"查询Alpha模拟状态统计时出错: {e}")
        return []


def query_checkable_alpha_stats(region: str = None, universe: str = None, delay: int = None, phase: str = None, sharp_threshold: float = 1.0, fitness_threshold: float = 0.8, passed: int = 0) -> List[Dict[str, Any]]:
    """
    查询可提交的Alpha统计数据（按分类分组）
    
    Args:
        region: 地区 (USA, EUR, ASI, CHN, GLB), None表示查询所有地区
        universe: 范围, None表示查询所有universe
        delay: 延迟, None表示查询所有delay
        phase: 阶段
        sharp_threshold: sharp阈值，默认为1.0
        fitness_threshold: fitness阈值，默认为0.8
        passed: passed状态，默认为0
        
    Returns:
        按分类分组的可提交Alpha统计结果
    """
    # 根据地区确定表名，如果region为None，则使用all_alphas表
    if region is None:
        table_name = "all_alphas"
    else:
        table_name = f"{region.lower()}_alphas"
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # 构建查询语句
        base_query = f"""
        WITH ranked_alphas AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY name
                       ORDER BY abs(sharp*fitness) DESC
                   ) AS rn
            FROM {table_name}  
            WHERE 1=1
        """
        params = []
        
        # 根据参数是否为None来决定是否添加查询条件
        if region is not None:
            base_query += " AND region = %s"
            params.append(region)
        if universe is not None:
            base_query += " AND universe = %s"
            params.append(universe)
        if delay is not None:
            base_query += " AND delay = %s"
            params.append(delay)
        if phase is not None:
            base_query += " AND phase = %s"
            params.append(phase)
        
        base_query += " AND simulated = 1"
        
        base_query += """
        )
        SELECT category, COUNT(*) as count FROM ranked_alphas 
        WHERE rn = 1 AND passed = %s AND sharp >= %s AND fitness >= %s
        GROUP BY category
        ORDER BY count DESC
        """
        
        params.extend([passed, sharp_threshold, fitness_threshold])
        cursor.execute(base_query, tuple(params))
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
    except Exception as e:
        print(f"查询可提交Alpha统计时出错: {e}")
        return []


def query_checkable_alpha_details(
        region: str = None, universe: str = None, delay: int = None, phase: str = None, category: str = None, sharp_threshold: float = 1.0, fitness_threshold: float = 0.8, passed: int = 0, neutralization: str = None
) -> List[Dict[str, Any]]:
    """
    查询指定分类下可提交的Alpha详细信息
    
    Args:
        region: 地区 (USA, EUR, ASI, CHN, GLB), None表示查询所有地区
        universe: 范围, None表示查询所有universe
        delay: 延迟, None表示查询所有delay
        phase: 阶段
        category: 分类，如果为None则查询所有分类
        sharp_threshold: sharp阈值，默认为1.0
        fitness_threshold: fitness阈值，默认为0.8
        passed: passed状态，默认为0
        neutralization: neutralization筛选条件，默认为None表示不筛选
        
    Returns:
        可提交Alpha的详细信息列表
    """
    # 根据地区确定表名，如果region为None，则使用all_alphas表
    if region is None:
        table_name = "all_alphas"
    else:
        table_name = f"{region.lower()}_alphas"
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # 构建查询语句
        base_query = f"""
        WITH ranked_alphas AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY name
                       ORDER BY abs(sharp*fitness) DESC
                   ) AS rn
            FROM {table_name}  
            WHERE 1=1
        """
        
        params = []
        
        # 根据参数是否为None来决定是否添加查询条件
        if region is not None:
            base_query += " AND region = %s"
            params.append(region)
        if universe is not None:
            base_query += " AND universe = %s"
            params.append(universe)
        if delay is not None:
            base_query += " AND delay = %s"
            params.append(delay)
        if phase is not None:
            base_query += " AND phase = %s"
            params.append(phase)
        
        base_query += " AND simulated = 1"
        
        # 如果指定了分类，则添加分类条件
        if category is not None:
            base_query += " AND category = %s"
            params.append(category)
            
        # 如果指定了neutralization，则添加筛选条件
        if neutralization is not None:
            base_query += " AND neutralization = %s"
            params.append(neutralization)
            
        params.extend([passed, sharp_threshold, fitness_threshold])
            
        base_query += """
        )
        SELECT * FROM ranked_alphas 
        WHERE rn = 1 AND passed = %s AND sharp >= %s AND fitness >= %s
        ORDER BY abs(sharp*fitness) DESC 
        LIMIT 500
        """
        
        cursor.execute(base_query, tuple(params))
        # logger.info('query_checkable_alpha_details SQL: %s', cursor.statement)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
    except Exception as e:
        logger.error(f"查询可检查Alpha详情时出错: {e}")
        return []


def query_submittable_alpha_stats(region: str = None, universe: str = None, delay: int = None, phase: str = None) -> List[Dict[str, Any]]:
    """
    查询可提交的Alpha统计数据（按分类分组）
    
    Args:
        region: 地区 (USA, EUR, ASI, CHN, GLB), None表示查询所有地区
        universe: 范围, None表示查询所有universe
        delay: 延迟, None表示查询所有delay
        phase: 阶段
        
    Returns:
        按分类分组的可提交Alpha统计结果
    """
    # 根据地区确定表名，如果region为None，则使用all_alphas表
    if region is None:
        table_name = "all_alphas"
    else:
        table_name = f"{region.lower()}_alphas"
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # 构建查询语句
        query = f"""
        SELECT category, COUNT(*) as count 
        FROM {table_name} 
        WHERE 1=1
        """
        params = []
        
        # 根据参数是否为None来决定是否添加查询条件
        if region is not None:
            query += " AND region = %s"
            params.append(region)
        if universe is not None:
            query += " AND universe = %s"
            params.append(universe)
        if delay is not None:
            query += " AND delay = %s"
            params.append(delay)
        if phase is not None:
            query += " AND phase = %s"
            params.append(phase)
        
        query += " AND passed = 1 AND submitted = 0"
        
        query += " GROUP BY category ORDER BY count DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
    except Exception as e:
        print(f"查询可提交Alpha统计时出错: {e}")
        return []


def query_submittable_alpha_details(region: str = None, universe: str = None, delay: int = None, phase: str = None, category: str = None) -> List[Dict[str, Any]]:
    """
    查询指定分类下可提交的Alpha详细信息
    
    Args:
        region: 地区 (USA, EUR, ASI, CHN, GLB), None表示查询所有地区
        universe: 范围, None表示查询所有universe
        delay: 延迟, None表示查询所有delay
        phase: 阶段
        category: 分类，如果为None则查询所有分类
        
    Returns:
        可提交Alpha的详细信息列表
    """
    # 根据地区确定表名，如果region为None，则使用all_alphas表
    if region is None:
        table_name = "all_alphas"
    else:
        table_name = f"{region.lower()}_alphas"
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # 构建查询语句
        base_query = f"""
        SELECT * 
        FROM {table_name} 
        WHERE 1=1
        """
        params = []
        
        # 根据参数是否为None来决定是否添加查询条件
        if region is not None:
            base_query += " AND region = %s"
            params.append(region)
        if universe is not None:
            base_query += " AND universe = %s"
            params.append(universe)
        if delay is not None:
            base_query += " AND delay = %s"
            params.append(delay)
        if phase is not None:
            base_query += " AND phase = %s"
            params.append(phase)
        
        base_query += " AND passed = 1 AND submitted = 0"
        
        # 如果指定了分类，则添加分类条件
        if category is not None:
            base_query += " AND category = %s"
            params.append(category)
            
        base_query += " ORDER BY abs(sharp*fitness) DESC LIMIT 50"
        
        cursor.execute(base_query, params)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
    except Exception as e:
        logger.error(f"查询可提交Alpha详情时出错: {e}")
        return []