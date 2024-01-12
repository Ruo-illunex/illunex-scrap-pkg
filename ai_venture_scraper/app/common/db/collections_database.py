from contextlib import contextmanager
from typing import List
import traceback

from sqlalchemy import create_engine
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

from app.config.settings import COLLECTIONS_DB_URL
from app.common.log.log_config import setup_logger
from app.config.settings import FILE_PATHS
from app.common.core.utils import get_current_datetime, make_dir
from app.models_init import (
    CollectVniaInfo, CollectVniaInfoPydantic,
    CollectVniaFinanceBalance, CollectVniaFinanceBalancePydantic,
    CollectVniaFinanceIncome, CollectVniaFinanceIncomePydantic,
    CollectVniaInvestmentInfo, CollectVniaInvestmentInfoPydantic,
    CollectVniaCertificate, CollectVniaCertificatePydantic,
)


class CollectionsDatabase:
    def __init__(self) -> None:
        self.engine = create_engine(COLLECTIONS_DB_URL, pool_recycle=3600, pool_size=20, max_overflow=0)
        self.SessionLocal = sessionmaker(bind=self.engine)
        file_path = FILE_PATHS["log"] + 'database'
        make_dir(file_path)
        file_path += f'/collections_{get_current_datetime()}.log'
        self.logger = setup_logger(
            "collections_database",
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

    def insert_vnia_info(self, data: CollectVniaInfoPydantic, session) -> str:
        """vnia_info 테이블에 데이터를 삽입하는 함수"""
        stmt = insert(CollectVniaInfo).values(**data.dict())
        stmt = stmt.on_duplicate_key_update(**data.dict())
        session.execute(stmt)

    def insert_vnia_finance_balance(self, data: List[CollectVniaFinanceBalancePydantic], session) -> str:
        """vnia_finance_balance 테이블에 데이터를 삽입하는 함수"""
        insert_data = [item.dict() for item in data]
        insert_stmt = insert(CollectVniaFinanceBalance).values(insert_data)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            **{c.name: c for c in insert_stmt.inserted.except_('biz_no')},
            )
        session.execute(on_duplicate_key_stmt)

    def insert_vnia_finance_income(self, data: List[CollectVniaFinanceIncomePydantic], session) -> str:
        """vnia_finance_income 테이블에 데이터를 삽입하는 함수"""
        insert_data = [item.dict() for item in data]
        insert_stmt = insert(CollectVniaFinanceIncome).values(insert_data)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            **{c.name: c for c in insert_stmt.inserted.except_('biz_no')},
        )
        session.execute(on_duplicate_key_stmt)

    def insert_vnia_investment(self, data: List[CollectVniaInvestmentInfoPydantic], session) -> str:
        """vnia_investment_info 테이블에 데이터를 삽입하는 함수"""
        insert_data = [item.dict() for item in data]
        insert_stmt = insert(CollectVniaInvestmentInfo).values(insert_data)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            **{c.name: c for c in insert_stmt.inserted.except_('biz_no')},
        )
        session.execute(on_duplicate_key_stmt)

    def insert_vnia_certificate(self, data: List[CollectVniaCertificatePydantic], session) -> str:
        """vnia_certificate 테이블에 데이터를 삽입하는 함수"""
        insert_data = [item.dict() for item in data]
        insert_stmt = insert(CollectVniaCertificate).values(insert_data)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            **{c.name: c for c in insert_stmt.inserted.except_('biz_no')},
        )
        session.execute(on_duplicate_key_stmt)

    def insert_all_vnia_data(
        self,
        vnia_info: CollectVniaInfoPydantic,
        vnia_finance_balance: List[CollectVniaFinanceBalancePydantic],
        vnia_finance_income: List[CollectVniaFinanceIncomePydantic],
        vnia_investment: List[CollectVniaInvestmentInfoPydantic],
        vnia_certificate: List[CollectVniaCertificatePydantic]
    ) -> None:
        """벤처기업 인증번호 정보, 재무정보, 투자정보, 인증정보를 DB에 삽입하는 함수"""
        status = False
        with self.get_session() as session:
            try:
                self.insert_vnia_info(vnia_info, session)
                self.insert_vnia_finance_balance(vnia_finance_balance, session)
                self.insert_vnia_finance_income(vnia_finance_income, session)
                self.insert_vnia_investment(vnia_investment, session)
                self.insert_vnia_certificate(vnia_certificate, session)
                
                status = True
                session.commit()
                msg = '벤처기업 인증번호 정보, 재무정보, 투자정보, 인증정보를 DB에 삽입하였습니다.'
                self.logger.info(msg)
            except SQLAlchemyError as e:
                session.rollback()
                msg = traceback.format_exc()
                self.logger.error(f'트랜잭션 에러: {e}\n{msg}')
            finally:
                session.close()
                return msg, status
