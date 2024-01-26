import os

# API URL 설정
NEWS_API_URL = os.getenv('NEWS_API_SERVER_URL')+'api/'
SCRAPE_API_URL = os.getenv('NEWS_API_SERVER_URL')+'scrape/'
OCR_API_URL = os.getenv('OCR_API_SERVER_URL')+'api/v1/'
AUTH_API_URL = os.getenv('AUTH_API_SERVER_URL')
