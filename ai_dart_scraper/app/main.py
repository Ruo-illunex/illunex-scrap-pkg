from typing import Optional
import traceback

from fastapi import FastAPI, Depends
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.common.log.log_config import setup_logger
from app.common.core.utils import get_current_datetime, make_dir
from app.models_init import *
from app.scrapers_init import *
from app.database_init import *
from app.common.db.base import BaseCollections, BaseCompanies
from app.api.dart_info_routers import router as dart_info_router
from app.api.dart_finance_routers import router as dart_finance_router
from app.config.settings import FILE_PATHS, SYNOLOGY_CHAT
from app.config.auth import verify_token


# 로거 설정
current_time = get_current_datetime()
file_path = FILE_PATHS["log"] + f'main_logger'
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
companies_db_engine = companies_db.engine

# DB 테이블 생성
BaseCollections.metadata.create_all(bind=collections_db_engine)
BaseCompanies.metadata.create_all(bind=companies_db_engine)


app = FastAPI()
app.include_router(dart_info_router, prefix="/api/v1")
app.include_router(dart_finance_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/scrape/dart_info")
async def scrape_dart_info(token: str = Depends(verify_token)):
    """OpenDartReader를 이용해 모든 기업의 기업 정보를 수집하는 함수"""
    try:
        scraper = DartInfoScraper()
        await scraper.scrape_dart_info()
        return {"status": "Scraping in progress..."}
    except Exception as e:
        err_msg = f"Error: {e}\n{traceback.format_exc()}"
        logger.error(err_msg)
        return {"status": err_msg}


@app.get("/scrape/dart_finance")
async def scrape_dart_finance(bsnsYear: Optional[int] = None, apiCallLimit: Optional[int] = 19000, token: str = Depends(verify_token)):
    """OpenDartReader를 이용해 모든 기업의 재무 정보를 수집하는 함수"""
    try:
        scraper = DartFinanceScraper(bsns_year=bsnsYear, api_call_limit=apiCallLimit)
        await scraper.scrape_dart_finance()
        return {"status": "Scraping in progress..."}
    except Exception as e:
        err_msg = f"Error: {e}\n{traceback.format_exc()}"
        logger.error(err_msg)
        return {"status": err_msg}


@app.get("/scrape/dart_notice")
async def scrape_dart_notice(startDt: Optional[str] = None, endDt: Optional[str] = None, apiCallLimit: Optional[int] = 19000, token: str = Depends(verify_token)):
    """OpenDartReader를 이용해 모든 기업의 공시 정보를 수집하는 함수"""
    try:
        scraper = DartNoticeScraper(api_call_limit=apiCallLimit)
        await scraper.scrape_dart_notice(start=startDt, end=endDt)
        return {"status": "Scraping in progress..."}
    except Exception as e:
        err_msg = f"Error: {e}\n{traceback.format_exc()}"
        logger.error(err_msg)
        return {"status": err_msg}


async def scrape_dart_info_task():
    """기업 정보 수집을 위한 비동기 작업"""
    try:
        scraper = DartInfoScraper()
        await scraper.scrape_dart_info()
    except Exception as e:
        err_msg = f"Error: {e}\n{traceback.format_exc()}"
        logger.error(err_msg)


async def scrape_dart_finance_task():
    """재무 정보 수집을 위한 비동기 작업"""
    try:
        scraper = DartFinanceScraper()
        await scraper.scrape_dart_finance()
    except Exception as e:
        err_msg = f"Error: {e}\n{traceback.format_exc()}"
        logger.error(err_msg)


# 스케줄러 설정
scheduler = AsyncIOScheduler()
scheduler.add_job(scrape_dart_info_task, 'cron', day=20)
scheduler.add_job(scrape_dart_finance_task, 'cron', day=20)
scheduler.start()
