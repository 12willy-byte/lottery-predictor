"""
数据库模块 - SQLite存储双色球和大乐透历史开奖数据
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "lottery.db")


def get_conn():
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表结构"""
    conn = get_conn()
    cursor = conn.cursor()

    # 双色球表: 6个红球(1-33) + 1个蓝球(1-16)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ssq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT UNIQUE NOT NULL,
            red1 INTEGER NOT NULL,
            red2 INTEGER NOT NULL,
            red3 INTEGER NOT NULL,
            red4 INTEGER NOT NULL,
            red5 INTEGER NOT NULL,
            red6 INTEGER NOT NULL,
            blue INTEGER NOT NULL,
            date TEXT,
            pool_amount TEXT,
            sale_amount TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 大乐透表: 5个前区(1-35) + 2个后区(1-12)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dlt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT UNIQUE NOT NULL,
            front1 INTEGER NOT NULL,
            front2 INTEGER NOT NULL,
            front3 INTEGER NOT NULL,
            front4 INTEGER NOT NULL,
            front5 INTEGER NOT NULL,
            back1 INTEGER NOT NULL,
            back2 INTEGER NOT NULL,
            date TEXT,
            pool_amount TEXT,
            sale_amount TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 统计数据缓存表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lottery_type TEXT NOT NULL,
            stats_data TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 更新日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS update_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lottery_type TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_ssq_data(data_list):
    """批量保存双色球数据"""
    conn = get_conn()
    cursor = conn.cursor()
    count = 0
    for d in data_list:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO ssq (period, red1, red2, red3, red4, red5, red6, blue, date, pool_amount, sale_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                d["period"],
                d["red1"], d["red2"], d["red3"], d["red4"], d["red5"], d["red6"],
                d["blue"], d.get("date"), d.get("pool_amount"), d.get("sale_amount")
            ))
            if cursor.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"  保存双色球 {d.get('period')} 失败: {e}")
    conn.commit()
    conn.close()
    return count


def save_dlt_data(data_list):
    """批量保存大乐透数据"""
    conn = get_conn()
    cursor = conn.cursor()
    count = 0
    for d in data_list:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO dlt (period, front1, front2, front3, front4, front5, back1, back2, date, pool_amount, sale_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                d["period"],
                d["front1"], d["front2"], d["front3"], d["front4"], d["front5"],
                d["back1"], d["back2"], d.get("date"), d.get("pool_amount"), d.get("sale_amount")
            ))
            if cursor.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"  保存大乐透 {d.get('period')} 失败: {e}")
    conn.commit()
    conn.close()
    return count


def get_all_ssq():
    """获取所有双色球数据，按期号排序"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ssq ORDER BY period ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_dlt():
    """获取所有大乐透数据，按期号排序"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dlt ORDER BY period ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_ssq():
    """获取最新双色球记录"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ssq ORDER BY period DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_latest_dlt():
    """获取最新大乐透记录"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dlt ORDER BY period DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_ssq_count():
    """获取双色球数据总数"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM ssq")
    row = cursor.fetchone()
    conn.close()
    return row["cnt"] if row else 0


def get_dlt_count():
    """获取大乐透数据总数"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM dlt")
    row = cursor.fetchone()
    conn.close()
    return row["cnt"] if row else 0


def log_update(lottery_type, status, message=""):
    """记录更新日志"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO update_log (lottery_type, status, message) VALUES (?, ?, ?)",
        (lottery_type, status, message)
    )
    conn.commit()
    conn.close()


def get_last_update_time(lottery_type):
    """获取最后更新时间"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT created_at FROM update_log WHERE lottery_type=? AND status='success' ORDER BY id DESC LIMIT 1",
        (lottery_type,)
    )
    row = cursor.fetchone()
    conn.close()
    return row["created_at"] if row else None


if __name__ == "__main__":
    init_db()
    print(f"数据库初始化完成: {DB_PATH}")
    print(f"双色球记录数: {get_ssq_count()}")
    print(f"大乐透记录数: {get_dlt_count()}")
