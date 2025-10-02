import streamlit as st
from typing import List, Dict, Any
import os
from brain_lit.svc.database import get_db_connection


def query_alphas_by_dataset(region: str, universe: str, delay: int, dataset: str) -> List[Dict[str, Any]]:
    """
    根据数据集查询Alpha记录
    
    Args:
        region: 地区 (USA, EUR, ASI, CHN, GLB)
        universe: 范围
        delay: 延迟
        dataset: 数据集ID
        
    Returns:
        匹配的Alpha记录列表
    """
    # 根据地区确定表名
    table_name = f"{region.lower()}_alphas"
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # 查询符合条件的Alpha记录
        query = f"""
        SELECT id, alpha, sharp, fitness, decay, neutralization, phase, created_at, updated_at 
        FROM {table_name} 
        WHERE universe = %s AND delay = %s AND dataset = %s
        ORDER BY sharp*fitness DESC
        LIMIT 100
        """
        cursor.execute(query, (universe, delay, dataset))
        
        # 获取结果
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
    except Exception as e:
        print(f"查询Alpha记录时出错: {e}")
        return []


def query_alphas_by_conditions(region: str, universe: str, delay: int, category: str = None) -> List[Dict[str, Any]]:
    """
    根据查询条件查询Alpha记录
    
    Args:
        region: 地区 (USA, EUR, ASI, CHN, GLB)
        universe: 范围
        delay: 延迟
        category: 分类（可选）
        
    Returns:
        匹配的Alpha记录列表
    """
    # 根据地区确定表名
    table_name = f"{region.lower()}_alphas"
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # 构建查询语句
        query = f"""
        SELECT id, alpha, sharp, fitness, decay, neutralization, phase, created_at, updated_at 
        FROM {table_name} 
        WHERE universe = %s AND delay = %s
        """
        params = [universe, delay]
        
        # 如果指定了分类，添加分类条件
        if category and category != "All":
            query += " AND category = %s"
            params.append(category.lower())
        
        query += " ORDER BY sharp*fitness DESC LIMIT 100"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
    except Exception as e:
        print(f"根据条件查询Alpha记录时出错: {e}")
        return []


def query_alphas_simulation_stats(region: str, universe: str, delay: int, category: str = None) -> List[Dict[str, Any]]:
    """
    按simulated值进行汇总统计
    
    Args:
        region: 地区 (USA, EUR, ASI, CHN, GLB)
        universe: 范围
        delay: 延迟
        category: 分类（可选）
        
    Returns:
        按simulated值分组的统计结果
    """
    # 根据地区确定表名
    table_name = f"{region.lower()}_alphas"
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # 构建统计查询语句
        query = f"""
        SELECT simulated, COUNT(*) as count
        FROM {table_name} 
        WHERE universe = %s AND delay = %s
        """
        params = [universe, delay]
        
        # 如果指定了分类，添加分类条件
        if category and category != "All":
            query += " AND category = %s"
            params.append(category.lower())
        
        query += " GROUP BY simulated ORDER BY count DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
    except Exception as e:
        print(f"查询Alpha模拟状态统计时出错: {e}")
        return []