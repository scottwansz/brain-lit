import mysql.connector
import streamlit as st


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