from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import timedelta, datetime
import glob
import os

import logging
from sqlalchemy.orm import Session
import pandas as pd

from app.models_init import ScrapManager, ScrapManagerPydantic, ScrapManagerWithIDPydantic, ScrapSessionLog, ScrapSessionLogPydantic, ScrapErrorLog, ScrapErrorLogPydantic
from app.common.db.scraper_manager_database import ScraperManagerDatabase
from app.common.log.log_config import setup_logger
from app.config.settings import FILE_PATHS


scraper_mng_db = ScraperManagerDatabase()

# 로거 생성
logger = setup_logger(
    'scrap_manager_router',
    'app/log/scrap_manager/scrap_manager_router.log',
    level=logging.INFO,
    backup_count=30,    # log 파일이 30개가 넘으면 이전 로그 파일을 삭제
    )

router = APIRouter()


@router.post(
        "/scrap_manager/",
        status_code=status.HTTP_201_CREATED,
        response_model=ScrapManagerPydantic
        )
def create_scrap_manager(
    scrap_manager_data: ScrapManagerPydantic,
    db: Session = Depends(scraper_mng_db.get_session_scraper_mng)
    ):
    """스크래핑 매니저에 새로운 레코드를 생성하는 엔드포인트
    args:
        scrap_manager_data (ScrapManagerPydantic): 스크래핑 매니저 데이터
        db (Session): DB 세션
    returns:
        new_scrap_manager (ScrapManagerPydantic): 새로운 스크래핑 매니저
    """

    # scrap_manager_data가 없는 경우에 대한 예외 처리
    if not scrap_manager_data:
        logger.error(f"[Fail] ScrapManager data not specified")
        raise HTTPException(status_code=400, detail="ScrapManager data not specified")
    
    # args의 type을 확인하는 예외 처리
    if not isinstance(scrap_manager_data, ScrapManagerPydantic):
        logger.error(f"[Fail] ScrapManager data is not ScrapManagerPydantic type")
        raise HTTPException(status_code=400, detail="ScrapManager data is not ScrapManagerPydantic type")
    
    # scrap_manager_data가 비어있는 경우에 대한 예외 처리
    if not scrap_manager_data.dict():
        logger.error(f"[Fail] ScrapManager data is empty")
        raise HTTPException(status_code=400, detail="ScrapManager data is empty")

    try:
        new_scrap_manager = ScrapManager(**scrap_manager_data.dict())
        db.add(new_scrap_manager)
        db.commit()
        db.refresh(new_scrap_manager)
        logger.info(f"[SUCCESS] Insert new data into scrap_manager: {scrap_manager_data.dict()}")
        return new_scrap_manager

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


async def get_scrap_managers_by_portal(portal: str, db: Session):
    """스크래핑 매니저 테이블에서 포털별 스크래핑 매니저를 가져오는 함수
    args:
        portal (str): 포털 이름
        db (Session): DB 세션
    returns:
        scrap_managers (list): 스크래핑 매니저 리스트
    """

    try:
        scrap_managers = db.query(ScrapManager).filter(ScrapManager.portal == portal).all()
        return [ScrapManagerWithIDPydantic.from_orm(scrap_manager) for scrap_manager in scrap_managers]

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get(
        "/scrap_manager/",
        response_model=List[ScrapManagerWithIDPydantic]
        )
async def get_scrap_managers_by_portal_endpoint(
    portal: str,
    db: Session = Depends(scraper_mng_db.get_session_scraper_mng)
    ):
    """스크래핑 매니저 테이블에서 포털별 스크래핑 매니저를 가져오는 엔드포인트
    args:
        portal (str): 포털 이름
        db (Session): DB 세션
    returns:
        scrap_managers (list): 스크래핑 매니저 리스트
    """
    
    # portal이 없는 경우에 대한 예외 처리
    if not portal:
        logger.error(f"[Fail] Portal not specified")
        raise HTTPException(status_code=400, detail="Portal not specified")

    return await get_scrap_managers_by_portal(portal, db) 


async def get_scrap_manager(id: int, db: Session):
    """스크래핑 매니저 테이블에서 스크래핑 매니저를 가져오는 함수
    args:
        id (int): 스크래핑 매니저 ID
        db (Session): DB 세션
    returns:
        scrap_manager (ScrapManagerPydantic): 스크래핑 매니저
    """

    try:
        scrap_manager = db.query(ScrapManager).filter(ScrapManager.id == id).first()

        if not scrap_manager:
            raise HTTPException(status_code=404, detail="ScrapManager not found")
        else:
            logger.info(f"scrap_manager: {scrap_manager}")
        return ScrapManagerPydantic.from_orm(scrap_manager)

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get(
        "/scrap_manager/{id}",
        response_model=ScrapManagerPydantic
        )
async def get_scrap_manager_endpoint(
    id: int,
    db: Session = Depends(scraper_mng_db.get_session_scraper_mng)
    ):
    """스크래핑 매니저 테이블에서 스크래핑 매니저를 가져오는 엔드포인트
    args:
        id (int): 스크래핑 매니저 ID
        db (Session): DB 세션
    returns:
        scrap_manager (ScrapManagerPydantic): 스크래핑 매니저
    """

    # id가 없는 경우에 대한 예외 처리
    if not id:
        logger.error(f"[Fail] ID not specified")
        raise HTTPException(status_code=400, detail="ID not specified")

    return await get_scrap_manager(id, db)


async def update_scrap_manager(
        id: int,
        scrap_manager_data: ScrapManagerPydantic,
        db: Session
        ):
    """스크래핑 매니저 테이블에서 스크래핑 매니저를 업데이트하는 함수
    args:
        id (int): 스크래핑 매니저 ID
        scrap_manager_data (ScrapManagerPydantic): 스크래핑 매니저 데이터
        db (Session): DB 세션
    returns:
        scrap_manager (ScrapManagerPydantic): 업데이트된 스크래핑 매니저
    """

    try:
        scrap_manager = db.query(ScrapManager).filter(ScrapManager.id == id).first()
        if not scrap_manager:
            raise HTTPException(status_code=404, detail="ScrapManager not found")

        for var, value in scrap_manager_data.dict().items():
            setattr(scrap_manager, var, value) if value is not None else None

        db.commit()
        return ScrapManagerPydantic.from_orm(scrap_manager)

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.put(
        "/scrap_manager/{id}",
        response_model=ScrapManagerPydantic
        )
async def update_scrap_manager_endpoint(
    id: int,
    scrap_manager_data: ScrapManagerPydantic,
    db: Session = Depends(scraper_mng_db.get_session_scraper_mng)
    ):
    """스크래핑 매니저 테이블에서 스크래핑 매니저를 업데이트하는 엔드포인트
    args:
        id (int): 스크래핑 매니저 ID
        scrap_manager_data (ScrapManagerPydantic): 스크래핑 매니저 데이터
        db (Session): DB 세션
    returns:
        scrap_manager (ScrapManagerPydantic): 업데이트된 스크래핑 매니저
    """

    # id가 없는 경우에 대한 예외 처리
    if not id:
        logger.error(f"[Fail] ID not specified")
        raise HTTPException(status_code=400, detail="ID not specified")
    
    # scrap_manager_data가 없는 경우에 대한 예외 처리
    if not scrap_manager_data:
        logger.error(f"[Fail] ScrapManager data not specified")
        raise HTTPException(status_code=400, detail="ScrapManager data not specified")
    
    # args의 type을 확인하는 예외 처리
    if not isinstance(scrap_manager_data, ScrapManagerPydantic):
        logger.error(f"[Fail] ScrapManager data is not ScrapManagerPydantic type")
        raise HTTPException(status_code=400, detail="ScrapManager data is not ScrapManagerPydantic type")
    
    # scrap_manager_data가 비어있는 경우에 대한 예외 처리
    if not scrap_manager_data.dict():
        logger.error(f"[Fail] ScrapManager data is empty")
        raise HTTPException(status_code=400, detail="ScrapManager data is empty")

    return await update_scrap_manager(id, scrap_manager_data, db)


async def delete_scrap_manager(id: int, db: Session):
    """스크래핑 매니저 테이블에서 스크래핑 매니저를 삭제하는 함수
    args:
        id (int): 스크래핑 매니저 ID
        db (Session): DB 세션
    """

    try:
        scrap_manager = db.query(ScrapManager).filter(ScrapManager.id == id).first()
        if not scrap_manager:
            raise HTTPException(status_code=404, detail="ScrapManager not found")

        db.delete(scrap_manager)
        db.commit()

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.delete(
        "/scrap_manager/{id}",
        status_code=status.HTTP_204_NO_CONTENT
        )
async def delete_scrap_manager_endpoint(
    id: int,
    db: Session = Depends(scraper_mng_db.get_session_scraper_mng)
    ):
    """스크래핑 매니저 테이블에서 스크래핑 매니저를 삭제하는 엔드포인트
    args:
        id (int): 스크래핑 매니저 ID
        db (Session): DB 세션
    """

    # id가 없는 경우에 대한 예외 처리
    if not id:
        logger.error(f"[Fail] ID not specified")
        raise HTTPException(status_code=400, detail="ID not specified")

    await delete_scrap_manager(id, db)


def get_scrap_session_logs_by_date(db: Session):
    """scrap_session_log 에서 최근 6시간 데이터를 조회하는 함수
    args:
        db (Session): DB 세션
    returns:
        scrap_session_logs (list): scrap_session_log 리스트
    """

    try:
        # 현재 시간
        current_time = datetime.now()
        # 1일 전 시간
        one_day_before = current_time - timedelta(hours=6)

        # scrap_session_log 테이블에서 1일 전부터 현재까지의 데이터를 조회
        scrap_session_logs = db.query(ScrapSessionLog).filter(ScrapSessionLog.start_time >= one_day_before).all()
        return scrap_session_logs

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def get_scrap_error_logs_by_date(db: Session):
    """scrap_error_log 에서 최근 6시간 데이터를 조회하는 함수
    args:
        db (Session): DB 세션
    returns:
        scrap_error_logs (list): scrap_error_log 리스트
    """

    try:
        # 현재 시간
        current_time = datetime.now()
        # 1일 전 시간
        one_day_before = current_time - timedelta(hours=6)

        # scrap_error_log 테이블에서 1일 전부터 현재까지의 데이터를 조회
        scrap_error_logs = db.query(ScrapErrorLog).filter(ScrapErrorLog.error_time >= one_day_before).all()
        return scrap_error_logs

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get(
        "/scrap_manager/monitoring/",
        response_model=dict
        )
async def get_scrap_manager_monitoring(
    db: Session = Depends(scraper_mng_db.get_session_scraper_mng)
    ):
    """스크래핑 매니저 모니터링 엔드포인트
    args:
        db (Session): DB 세션
    returns:
        monitoring_data (dict): 모니터링 데이터
    """

    try:
        # scrap_session_log 테이블에서 최근 1일 데이터를 조회
        scrap_session_logs = get_scrap_session_logs_by_date(db)
        # scrap_error_log 테이블에서 최근 1일 데이터를 조회
        scrap_error_logs = get_scrap_error_logs_by_date(db)

        # 모니터링 데이터
        monitoring_data = {
            "scrap_session_logs": [ScrapSessionLogPydantic.from_orm(scrap_session_log).dict() for scrap_session_log in scrap_session_logs] if scrap_session_logs else [],
            "scrap_error_logs": [ScrapErrorLogPydantic.from_orm(scrap_error_log).dict() for scrap_error_log in scrap_error_logs] if scrap_error_logs else [],
            }

        return monitoring_data

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/data/{portal}/")
def get_csv_data(portal: str):
    """CSV 파일을 읽어서 데이터를 가져오는 엔드포인트
    args:
        portal (str): 포털 이름
    returns:
        data (json): CSV 파일의 데이터
    """

    # portal이 없는 경우에 대한 예외 처리
    if not portal:
        logger.error(f"[Fail] Portal not specified")
        raise HTTPException(status_code=400, detail="Portal not specified")

    try:
        # CSV 파일 경로
        file_path = FILE_PATHS.get(f'{portal}_links_csv')
        file_list = glob.glob(file_path)

        # CSV 파일이 존재하는 경우
        if file_list:
            file_list.sort(key=lambda x: os.path.splitext(os.path.basename(x))[0][-14:])
            latest_file = file_list[-1]
            # json 파일로 변환
            data = pd.read_csv(latest_file).to_json(orient='records')
            return data
        
        # CSV 파일이 존재하지 않는 경우
        else:
            logger.error(f"[Fail] CSV file not found")
            raise HTTPException(status_code=404, detail="CSV file not found")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
