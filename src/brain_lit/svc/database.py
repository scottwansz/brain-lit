import streamlit as st
import mysql.connector
from typing import Set, List
import os


def get_db_connection():
    """
    创建并返回数据库连接
    """
    try:
        connection = mysql.connector.connect(
            host=st.secrets["mysql"]["host"],
            port=st.secrets["mysql"]["port"],
            database=st.secrets["mysql"]["database"],
            user=st.secrets["mysql"]["username"],
            password=st.secrets["mysql"]["password"]
        )
        return connection
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None


def get_used_datasets(region: str, universe: str, delay: int) -> Set[str]:
    """
    从数据库获取已使用的数据集ID集合
    
    Args:
        region: 区域参数
        universe: 范围参数
        delay: 延迟参数
        
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
        WHERE region = %s AND universe = %s AND delay = %s
        """
        cursor.execute(query, (region, universe, delay))
        
        # 获取结果
        used_datasets = set()
        for (dataset_id,) in cursor.fetchall():
            used_datasets.add(dataset_id)
        
        cursor.close()
        connection.close()
        
        return used_datasets
    except Exception as e:
        print(f"查询已使用的数据集时出错: {e}")
        return set()