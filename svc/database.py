from typing import Dict, Any, List, Optional

import mysql.connector
import streamlit as st

from svc.logger import setup_logger

logger = setup_logger(__name__)


# @st.cache_resource
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

def query_by_sql(sql: str) -> List[Dict[str, Any]]:
    """
    :param sql:
    :return:
    """
    try:
        connection = get_db_connection()
        if not connection:
            return []
        cursor = connection.cursor(dictionary=True)
        cursor.execute(sql)
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"查询数据库时出错: {e}")
        return []

def query_table(table_name: str, conditions: Dict[str, Any], limit: Optional[int] = 2000, offset: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    通用的数据库查询方法
    
    Args:
        table_name: 表名
        conditions: 查询条件字典，例如 {'region': 'JPN', 'universe': 'TOP1600', 'delay': 0}
                    如果值是列表，则使用IN操作符
        limit: 限制返回记录数
        offset: 偏移量，用于分页
    
    Returns:
        查询结果列表，每个元素是一个字典，表示一行记录
    """
    try:
        connection = get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor(dictionary=True)
        
        # 构建WHERE子句
        where_clauses = []
        params = []
        
        for key, value in conditions.items():
            if value is not None:
                # 如果值是列表，使用IN操作符
                if isinstance(value, list):
                    if value:  # 确保列表不为空
                        placeholders = ','.join(['%s'] * len(value))
                        where_clauses.append(f"{key} IN ({placeholders})")
                        params.extend(value)
                    else:
                        # 如果列表为空，则不添加此条件
                        pass
                else:
                    # 单个值使用=操作符
                    where_clauses.append(f"{key} = %s")
                    params.append(value)
            # 如果值为None，则跳过此条件，不添加到查询中
        
        # 构建SQL查询语句
        query = f"SELECT * FROM {table_name}"
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY region"

        # 添加LIMIT和OFFSET
        if limit is not None:
            query += f" LIMIT {limit}"
            if offset is not None:
                query += f" OFFSET {offset}"
        
        # 执行查询
        cursor.execute(query, params)
        logger.info(f"Executing query: {cursor.statement}")
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return results
    
    except Exception as e:
        print(f"查询数据库时出错: {e}")
        return []


def update_table(table_name: str, conditions: Dict[str, Any], updates: Dict[str, Any]) -> int:
    """
    通用的数据更新方法
    
    Args:
        table_name: 表名
        conditions: 更新条件字典，用于确定哪些记录需要被更新
        updates: 更新字段字典，键为字段名，值为要更新的值
                例如: {'conditions': {'id': 1}, 'updates': {'name': 'new_name'}}
    
    Returns:
        受影响的行数
    """
    try:
        connection = get_db_connection()
        if not connection:
            return 0
        
        cursor = connection.cursor()
        
        # 构建SET子句
        set_clauses = []
        update_params = []
        
        for key, value in updates.items():
            set_clauses.append(f"{key} = %s")
            update_params.append(value)
        
        # 构建WHERE子句
        where_clauses = []
        condition_params = []
        
        for key, value in conditions.items():
            if value is not None:
                # 如果值是列表，使用IN操作符
                if isinstance(value, list):
                    if value:  # 确保列表不为空
                        placeholders = ','.join(['%s'] * len(value))
                        where_clauses.append(f"{key} IN ({placeholders})")
                        condition_params.extend(value)
                    else:
                        # 如果列表为空，则不添加此条件
                        pass
                else:
                    # 单个值使用=操作符
                    where_clauses.append(f"{key} = %s")
                    condition_params.append(value)
            # 如果值为None，则跳过此条件，不添加到查询中
        
        # 构建完整的UPDATE语句
        set_clause = ", ".join(set_clauses)
        where_clause = " AND ".join(where_clauses)
        
        query = f"UPDATE {table_name} SET {set_clause}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        # 合并参数
        params = update_params + condition_params
        
        # 执行更新
        cursor.execute(query, params)
        affected_rows = cursor.rowcount
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return affected_rows
    
    except Exception as e:
        print(f"更新数据库时出错: {e}")
        return 0


def batch_update_table(table_name: str, updates: List[Dict[str, Any]]) -> int:
    """
    批量更新数据方法
    
    Args:
        table_name: 表名
        updates: 更新操作列表，每个元素是一个字典，包含'conditions'和'updates'两个键
                例如: [{'conditions': {'id': 1}, 'updates': {'name': 'new_name'}},
                      {'conditions': {'id': 2}, 'updates': {'name': 'another_name'}}]
    
    Returns:
        所有更新操作影响的总行数
    """
    try:
        connection = get_db_connection()
        if not connection:
            return 0
        
        cursor = connection.cursor()
        
        total_affected_rows = 0
        
        for update_item in updates:
            conditions = update_item.get('conditions', {})
            updates_data = update_item.get('updates', {})
            
            # 构建SET子句
            set_clauses = []
            update_params = []
            
            for key, value in updates_data.items():
                set_clauses.append(f"{key} = %s")
                update_params.append(value)
            
            # 构建WHERE子句
            where_clauses = []
            condition_params = []
            
            for key, value in conditions.items():
                if value is not None:
                    # 如果值是列表，使用IN操作符
                    if isinstance(value, list):
                        if value:  # 确保列表不为空
                            placeholders = ','.join(['%s'] * len(value))
                            where_clauses.append(f"{key} IN ({placeholders})")
                            condition_params.extend(value)
                        else:
                            # 如果列表为空，则不添加此条件
                            pass
                    else:
                        # 单个值使用=操作符
                        where_clauses.append(f"{key} = %s")
                        condition_params.append(value)
                else:
                    # 处理为NULL的情况
                    where_clauses.append(f"{key} IS NULL")
            
            # 构建完整的UPDATE语句
            set_clause = ", ".join(set_clauses)
            where_clause = " AND ".join(where_clauses)
            
            query = f"UPDATE {table_name} SET {set_clause}"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            # 合并参数
            params = update_params + condition_params
            
            # 执行更新
            cursor.execute(query, params)
            total_affected_rows += cursor.rowcount
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return total_affected_rows
    
    except Exception as e:
        print(f"批量更新数据库时出错: {e}")
        return 0


def insert_record(table_name: str, data: Dict[str, Any]) -> int:
    """
    通用的数据插入方法
    
    Args:
        table_name: 表名
        data: 要插入的数据字典，键为字段名，值为要插入的值
              例如: {'name': 'example', 'age': 25, 'email': 'test@example.com'}
    
    Returns:
        受影响的行数(通常为1)
    """
    try:
        connection = get_db_connection()
        if not connection:
            return 0
        
        cursor = connection.cursor()
        
        # 构建INSERT语句
        columns = list(data.keys())
        values = list(data.values())
        
        column_names = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
        
        # 执行插入
        cursor.execute(query, values)
        affected_rows = cursor.rowcount
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return affected_rows
    
    except Exception as e:
        print(f"插入数据时出错: {e}")
        return 0


def batch_insert_records(table_name: str, data_list: List[Dict[str, Any]]) -> int:
    """
    通用的批量数据插入方法
    
    Args:
        table_name: 表名
        data_list: 要插入的数据字典列表，每个元素是一个字典
                  例如: [{'name': 'example1', 'age': 25}, {'name': 'example2', 'age': 30}]
    
    Returns:
        受影响的行数
    """
    try:
        connection = get_db_connection()
        if not connection:
            return 0
        
        cursor = connection.cursor()
        
        total_affected_rows = 0
        
        # 检查是否有数据需要插入
        if not data_list:
            return 0
        
        # 获取字段名（假设所有字典具有相同的键）
        columns = list(data_list[0].keys())
        column_names = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        # 构建INSERT语句
        query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
        
        # 为每个数据字典执行插入
        for data in data_list:
            values = [data[col] for col in columns]
            cursor.execute(query, values)
            total_affected_rows += cursor.rowcount
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return total_affected_rows
    
    except Exception as e:
        print(f"批量插入数据时出错: {e}")
        return 0
