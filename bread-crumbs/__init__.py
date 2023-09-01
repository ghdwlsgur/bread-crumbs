from flask import Flask
from . import config
import pymysql


def get_db_connection():
    connection = pymysql.connect(
        user=config.db['user'],
        password=config.db['password'],
        host=config.db['host'],
        port=config.db['port'],
        db=config.db['database'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection


def create_app():
    app = Flask(__name__)
    print(config.db)
    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = "SELECT * FROM user;"
        cursor.execute(sql)
        result = cursor.fetchall()
    conn.close()

    print(result)

    return app
