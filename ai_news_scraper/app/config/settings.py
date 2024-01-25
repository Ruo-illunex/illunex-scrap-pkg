import os
from dotenv import load_dotenv

# 실행 환경 결정 (예: 'dev', 'prod')
env = os.getenv('ENVIRONMENT')

# .env 파일 경로 설정
env_file = f'.env.{env}'

# .env 파일 로드
load_dotenv(env_file)

# 환경 변수에서 데이터베이스 설정값 읽기
username = os.getenv('DB_USERNAME')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
news_database = os.getenv('NEWS_DB_DATABASE')
scraper_mng_database = os.getenv('SCRAPER_MNG_DB_DATABASE')
api_server_host = os.getenv('API_SERVER_HOST')
api_server_port = os.getenv('API_SERVER_PORT')

# DB 및 API 서버 URL 구성
NEWS_DB_URL = f'mysql+pymysql://{username}:{password}@{host}:{port}/{news_database}?charset=utf8mb4'
SCRAPER_MNG_DB_URL = f'mysql+pymysql://{username}:{password}@{host}:{port}/{scraper_mng_database}?charset=utf8mb4'
API_SERVER_URL = f'http://{api_server_host}:{api_server_port}/api/scrap_manager/'

# 파일 경로
FILE_PATHS = {
    'category':'app/common/core/category.yaml',
    'chromedriver': 'app/config/chromedriver',
    'esg_finance_hub_links_csv': 'app/data/esg_finance_hub_links_*.csv',
    'esg_finance_media': 'app/common/core/esg_finance_media.yaml',
    'data': 'app/data',
    }


# 시놀로지 챗봇 설정
SYNOLOGY_CHAT = {
    'api_url': os.getenv('SYNOLOGY_CHAT_API_URL'),
    'prod_token': os.getenv('SYNOLOGY_CHAT_PROD_TOKEN'),
    'dev_token': os.getenv('SYNOLOGY_CHAT_DEV_TOKEN'),
    'test_token': os.getenv('SYNOLOGY_CHAT_TEST_TOKEN')
}
