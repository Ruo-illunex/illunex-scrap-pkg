from typing import Optional
import traceback

from fastapi import FastAPI, Depends
from apscheduler.schedulers.background import BackgroundScheduler

from app.common.log.log_config import setup_logger
from app.common.core.utils import get_current_datetime, make_dir
from app.models_init import *
from app.scrapers_init import *
from app.database_init import *
from app.common.db.base import BaseCollections
from app.config.settings import FILE_PATHS, SYNOLOGY_CHAT
from app.config.auth import verify_token


# 로거 설정
current_time = get_current_datetime()
file_path = FILE_PATHS["log"] + 'main_logger'
make_dir(file_path)
file_path += f'/main_{current_time}.log'
logger = setup_logger(
    "main_logger",
    file_path,
)

# 시놀로지 챗봇 설정    -> ** 추후 시놀로지 챗봇으로 알림기능 추가 **
prod_token = SYNOLOGY_CHAT['prod_token']
dev_token = SYNOLOGY_CHAT['dev_token']
test_token = SYNOLOGY_CHAT['test_token']

# DB 연결
collections_db_engine = collections_db.engine

# DB 테이블 생성
BaseCollections.metadata.create_all(bind=collections_db_engine)

app = FastAPI()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/scrape/vntr")
def scrape_vntr(token: str = Depends(verify_token)):
    """VntrScraper를 이용해 모든 기업의 기업 정보를 수집하는 함수"""
    try:
        scraper = VntrScraper()
        vntr_list = scraper._get_vntr_list()
        scraper.scrape(vntr_list=vntr_list)
        return {"status": "Scraping in progress..."}
    except Exception as e:
        err_msg = f"Error: {e}\n{traceback.format_exc()}"
        logger.error(err_msg)
        return {"status": "Scraping failed..."}
    finally:
        logger.info("Scraping completed...")
        logger.info("--------------------------------------------------")


def scrape_vntr_task():
    """VntrScraper를 이용해 모든 기업의 기업 정보를 수집하는 함수를 주기적으로 실행하는 함수"""
    try:
        logger.info("Scraping started...")
        scraper = VntrScraper()
        vntr_list = scraper._get_vntr_list()
        scraper.scrape(vntr_list=vntr_list)
    except Exception as e:
        err_msg = f"Error: {e}\n{traceback.format_exc()}"
        logger.error(err_msg)
        logger.info("Scraping failed...")
        logger.info("--------------------------------------------------")
    finally:
        logger.info("Scraping completed...")
        logger.info("--------------------------------------------------")


# 스케줄러 인스턴스 생성
scheduler = BackgroundScheduler()

# 매달 5일마다 `scrape_vntr_task` 함수를 실행하는 작업 추가
scheduler.add_job(scrape_vntr_task, 'cron', day=5)

# 스케줄러 시작
scheduler.start()
