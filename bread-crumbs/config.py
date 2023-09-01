import os

BASE_DIR = os.path.dirname(__file__)

# 데이터베이스 접속 정보
db = {
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT',  3306)),
    'database': os.getenv('MYSQL_DATABASE', 'PROJECT')
}
