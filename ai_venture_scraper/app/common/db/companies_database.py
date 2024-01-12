import traceback
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

from app.config.settings import COMPANIES_DB_URL
from app.common.log.log_config import setup_logger
from app.config.settings import FILE_PATHS
from app.common.core.utils import get_current_datetime, make_dir
from app.models_init import NewCompanyInfo


class CompaniesDatabase:
    def __init__(self) -> None:
        self.engine = create_engine(COMPANIES_DB_URL, pool_recycle=3600, pool_size=20, max_overflow=0)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        file_path = FILE_PATHS['log'] + 'database'
        make_dir(file_path)
        file_path += f'/companies_{get_current_datetime()}.log'
        self.logger = setup_logger(
            "companies_database",
            file_path
        )

    @contextmanager
    def get_session(self):
        """세션 컨텍스트 매니저"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_company_id_df(self) -> None:
        """기업 정보를 조회하는 함수"""
        with self.get_session() as session:
            try:
                existing_data = session.query(NewCompanyInfo.biz_num, NewCompanyInfo.id).all()
                df = pd.DataFrame(existing_data, columns=['biz_num', 'id'])
                return df
            except SQLAlchemyError as e:
                err_msg = traceback.format_exc()
                self.logger.error(f"Error: {e}\n{err_msg}")
                return None
