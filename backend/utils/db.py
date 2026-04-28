"""
数据库连接工具
"""
import pymysql
import os
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()


def get_db_config():
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'caviar_crm'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }


@contextmanager
def get_connection():
    """上下文管理器获取数据库连接"""
    config = get_db_config()
    conn = pymysql.connect(**config)
    try:
        yield conn
    finally:
        conn.close()


def execute_query(sql, params=None):
    """执行查询并返回结果"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def execute_write(sql, params=None):
    """执行写操作并提交"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
