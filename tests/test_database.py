import unittest
import mysql.connector
import streamlit as st
from typing import Dict, Any, List

from brain_lit.svc.database import insert_record, batch_insert_records, query_table, update_table


class TestDatabaseOperations(unittest.TestCase):
    """测试数据库操作方法"""

    @classmethod
    def setUpClass(cls):
        """在所有测试开始前创建测试表"""
        try:
            # 连接数据库
            connection = mysql.connector.connect(
                host=st.secrets["mysql"]["host"],
                port=st.secrets["mysql"]["port"],
                database=st.secrets["mysql"]["database"],
                user=st.secrets["mysql"]["username"],
                password=st.secrets["mysql"]["password"]
            )
            
            cursor = connection.cursor()
            
            # 创建测试表
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS test_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                age INT,
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_sql)
            
            connection.commit()
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"创建测试表时出错: {e}")

    @classmethod
    def tearDownClass(cls):
        """在所有测试结束后删除测试表"""
        try:
            # 连接数据库
            connection = mysql.connector.connect(
                host=st.secrets["mysql"]["host"],
                port=st.secrets["mysql"]["port"],
                database=st.secrets["mysql"]["database"],
                user=st.secrets["mysql"]["username"],
                password=st.secrets["mysql"]["password"]
            )
            
            cursor = connection.cursor()
            
            # 删除测试表
            drop_table_sql = "DROP TABLE IF EXISTS test_users"
            cursor.execute(drop_table_sql)
            
            connection.commit()
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"删除测试表时出错: {e}")

    def setUp(self):
        """在每个测试方法开始前执行，清理测试表数据"""
        try:
            connection = mysql.connector.connect(
                host=st.secrets["mysql"]["host"],
                port=st.secrets["mysql"]["port"],
                database=st.secrets["mysql"]["database"],
                user=st.secrets["mysql"]["username"],
                password=st.secrets["mysql"]["password"]
            )
            
            cursor = connection.cursor()
            
            # 清空测试表数据
            truncate_table_sql = "TRUNCATE TABLE test_users"
            cursor.execute(truncate_table_sql)
            
            connection.commit()
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"清空测试表数据时出错: {e}")

    def test_insert_record(self):
        """测试插入单条记录方法"""
        # 准备测试数据
        test_data = {
            'name': '张三',
            'age': 25,
            'email': 'zhangsan@example.com'
        }
        
        # 执行插入操作
        affected_rows = insert_record('test_users', test_data)
        
        # 验证返回结果
        self.assertEqual(affected_rows, 1)
        
        # 验证数据确实插入成功
        results = query_table('test_users', {'name': '张三'})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], '张三')
        self.assertEqual(results[0]['age'], 25)
        self.assertEqual(results[0]['email'], 'zhangsan@example.com')

    def test_batch_insert_records(self):
        """测试批量插入记录方法"""
        # 准备测试数据
        test_data_list = [
            {'name': '张三', 'age': 25, 'email': 'zhangsan@example.com'},
            {'name': '李四', 'age': 30, 'email': 'lisi@example.com'},
            {'name': '王五', 'age': 35, 'email': 'wangwu@example.com'}
        ]
        
        # 执行批量插入操作
        affected_rows = batch_insert_records('test_users', test_data_list)
        
        # 验证返回结果
        self.assertEqual(affected_rows, 3)
        
        # 验证数据确实插入成功
        results = query_table('test_users', {})
        self.assertEqual(len(results), 3)
        
        # 验证每条记录的字段值
        names = [result['name'] for result in results]
        self.assertIn('张三', names)
        self.assertIn('李四', names)
        self.assertIn('王五', names)

    def test_insert_and_query_with_conditions(self):
        """测试插入数据后使用条件查询"""
        # 插入测试数据
        test_data_list = [
            {'name': '赵六', 'age': 28, 'email': 'zhaoliu@example.com'},
            {'name': '钱七', 'age': 32, 'email': 'qianqi@example.com'}
        ]
        
        batch_insert_records('test_users', test_data_list)
        
        # 使用条件查询
        results = query_table('test_users', {'age': 28})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], '赵六')
        
        # 测试范围查询（大于）
        results = query_table('test_users', {'age': [28, 32]}, limit=10)
        self.assertEqual(len(results), 2)

    def test_update_after_insert(self):
        """测试插入数据后进行更新操作"""
        # 插入测试数据
        test_data = {'name': '测试用户', 'age': 20, 'email': 'test@example.com'}
        insert_record('test_users', test_data)
        
        # 更新数据
        affected_rows = update_table('test_users', {'name': '测试用户'}, {'age': 25})
        self.assertEqual(affected_rows, 1)
        
        # 验证更新结果
        results = query_table('test_users', {'name': '测试用户'})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['age'], 25)


if __name__ == '__main__':
    unittest.main()