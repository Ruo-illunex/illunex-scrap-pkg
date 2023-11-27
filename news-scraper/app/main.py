from fastapi import FastAPI
import schedule
import time
import datetime
import threading

from app.scrap_manager.api.router import router as scrap_manager_router
from app.common.db.news_database import NewsDatabase
from app.common.db.scraper_manager_database import ScraperManagerDatabase
from app.common.db.base import BaseScraper, BaseManager
from app.models_init import *
import app.scrapers_init as scraper
from app.config.settings import SYNOLOGY_CHAT
from app.notification.synology_chat import send_message_to_synology_chat
from app.notification.statistics import create_daily_message, create_error_report_message
from app.common.log.log_config import setup_logger


# 로거 설정
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
logger = setup_logger(
    "main_logger",
    f'app/log/main_logger/main_logger_{current_time}.log',
    level='INFO',
)

# 시놀로지 챗봇 설정
prod_token = SYNOLOGY_CHAT['prod_token']
dev_token = SYNOLOGY_CHAT['dev_token']
test_token = SYNOLOGY_CHAT['test_token']

# DB 연결
news_scraper_engine = NewsDatabase().engine
scraper_mng_engine = ScraperManagerDatabase().engine

# DB 테이블 생성
BaseScraper.metadata.create_all(bind=news_scraper_engine)
BaseManager.metadata.create_all(bind=scraper_mng_engine)

app = FastAPI()
app.include_router(scrap_manager_router, tags=["scrap_manager"], prefix="/api")


@app.get("/scrape")
async def root():
    return {"message": "Illunex News Scraper"}


@app.get("/scrape/daum_news")
async def scrape_daum_news_endpoint():
    """다음 뉴스 스크래핑을 시작하는 엔드포인트"""

    try:
        await scraper.scrape_daum_news()
        return {"message": "Daum News Scraping Started"}

    except Exception as e:
        logger.error(f"Error: {e}")
        syn_err_msg = create_error_report_message(e, "daum")
        send_message_to_synology_chat(syn_err_msg, dev_token)
        return {"message": f"Error: {e}"}


@app.get("/scrape/naver_news")
async def scrape_naver_news_endpoint():
    """네이버 뉴스 스크래핑을 시작하는 엔드포인트"""

    try:
        await scraper.scrape_naver_news()
        return {"message": "Naver News Scraping Started"}

    except Exception as e:
        logger.error(f"Error: {e}")
        syn_err_msg = create_error_report_message(e, "naver")
        send_message_to_synology_chat(syn_err_msg, dev_token)
        return {"message": f"Error: {e}"}


@app.get("/scrape/zdnet_news")
async def scrape_zdnet_news_endpoint():
    """ZDNet 뉴스 스크래핑을 시작하는 엔드포인트"""

    try:
        await scraper.scrape_zdnet_news()
        return {"message": "ZDNet News Scraping Started"}

    except Exception as e:
        logger.error(f"Error: {e}")
        syn_err_msg = create_error_report_message(e, "zdnet")
        send_message_to_synology_chat(syn_err_msg, dev_token)
        return {"message": f"Error: {e}"}


@app.get("/scrape/vs_news")
async def scrape_vs_news_endpoint():
    """Venture Square 뉴스 스크래핑을 시작하는 엔드포인트"""

    try:
        await scraper.scrape_vs_news()
        return {"message": "Venture Square News Scraping Started"}

    except Exception as e:
        logger.error(f"Error: {e}")
        syn_err_msg = create_error_report_message(e, "venturesquare")
        send_message_to_synology_chat(syn_err_msg, dev_token)
        return {"message": f"Error: {e}"}


@app.get("/scrape/thebell_news")
async def scrape_thebell_news_endpoint():
    """The bell 뉴스 스크래핑을 시작하는 엔드포인트"""

    try:
        await scraper.scrape_thebell_news()
        return {"message": "The Bell News Scraping Started"}
    
    except Exception as e:
        logger.error(f"Error: {e}")
        syn_err_msg = create_error_report_message(e, "thebell")
        send_message_to_synology_chat(syn_err_msg, dev_token)
        return {"message": f"Error: {e}"}


@app.get("/scrape/startupn_news")
async def scrape_startupn_news_endpoint():
    """Startupn 뉴스 스크래핑을 시작하는 엔드포인트"""

    try:
        await scraper.scrape_startupn_news()
        return {"message": "Startupn News Scraping Started"}
    
    except Exception as e:
        logger.error(f"Error: {e}")
        syn_err_msg = create_error_report_message(e, "startupn")
        send_message_to_synology_chat(syn_err_msg, dev_token)
        return {"message": f"Error: {e}"}


@app.get("/scrape/startuptoday_news")
async def scrape_startuptoday_news_endpoint():
    """StartupToday 뉴스 스크래핑을 시작하는 엔드포인트"""

    try:
        await scraper.scrape_startuptoday_news()
        return {"message": "StartupToday News Scraping Started"}
    
    except Exception as e:
        logger.error(f"Error: {e}")
        syn_err_msg = create_error_report_message(e, "startuptoday")
        send_message_to_synology_chat(syn_err_msg, dev_token)
        return {"message": f"Error: {e}"}


@app.get("/scrape/platum_news")
async def scrape_platum_news_endpoint():
    """Platum 뉴스 스크래핑을 시작하는 엔드포인트"""

    try:
        await scraper.scrape_platum_news()
        return {"message": "Platum News Scraping Started"}
    
    except Exception as e:
        logger.error(f"Error: {e}")
        syn_err_msg = create_error_report_message(e, "platum")
        send_message_to_synology_chat(syn_err_msg, dev_token)
        return {"message": f"Error: {e}"}


# 스케줄러 관련 코드
def scheduled_job():
    try:
        message = create_daily_message()
        send_message_to_synology_chat(message, prod_token)    # 실제 운영 환경에서는 prod_token 사용
        # send_message_to_synology_chat(message, test_token)  # 테스트용
        logger.info("Statistics Message Sent")

    except Exception as e:
        logger.error(f"Error: {e}")

schedule.every().day.at("00:00").do(scheduled_job)
# schedule.every(1).minutes.do(scheduled_job) # 테스트용


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# 스케줄러를 별도의 스레드에서 실행
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()
