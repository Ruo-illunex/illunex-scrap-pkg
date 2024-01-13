from contextlib import contextmanager
from typing import List, Optional
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
    CollectVntrInfo, CollectVntrInfoPydantic,
    CollectVntrFinanceBalance, CollectVntrFinanceBalancePydantic,
    CollectVntrFinanceIncome, CollectVntrFinanceIncomePydantic,
    CollectVntrInvestmentInfo, CollectVntrInvestmentInfoPydantic,
    CollectVntrCertificate, CollectVntrCertificatePydantic,
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

    def insert_vntr_info(self, data: CollectVntrInfoPydantic, session) -> str:
        """vntr_info 테이블에 데이터를 삽입하는 함수"""
        insert_stmt = insert(CollectVntrInfo).values(**data.dict())
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            **{c.name: c for c in insert_stmt.table.c if c.name != 'id'}
            )
        session.execute(on_duplicate_key_stmt)

    def insert_vntr_finance_balance(self, data: List[CollectVntrFinanceBalancePydantic], session) -> str:
        """vntr_finance_balance 테이블에 데이터를 삽입하는 함수"""
        insert_data = [item.dict() for item in data]
        insert_stmt = insert(CollectVntrFinanceBalance).values(insert_data)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            **{c.name: c for c in insert_stmt.table.c if c.name != 'id'}
            )
        session.execute(on_duplicate_key_stmt)

    def insert_vntr_finance_income(self, data: List[CollectVntrFinanceIncomePydantic], session) -> str:
        """vntr_finance_income 테이블에 데이터를 삽입하는 함수"""
        insert_data = [item.dict() for item in data]
        insert_stmt = insert(CollectVntrFinanceIncome).values(insert_data)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            **{c.name: c for c in insert_stmt.table.c if c.name != 'id'}
        )
        session.execute(on_duplicate_key_stmt)

    def insert_vntr_investment(self, data: List[CollectVntrInvestmentInfoPydantic], session) -> str:
        """vntr_investment_info 테이블에 데이터를 삽입하는 함수"""
        insert_data = [item.dict() for item in data]
        insert_stmt = insert(CollectVntrInvestmentInfo).values(insert_data)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            **{c.name: c for c in insert_stmt.table.c if c.name != 'id'}
        )
        session.execute(on_duplicate_key_stmt)

    def insert_vntr_certificate(self, data: List[CollectVntrCertificatePydantic], session) -> str:
        """vntr_certificate 테이블에 데이터를 삽입하는 함수"""
        insert_data = [item.dict() for item in data]
        insert_stmt = insert(CollectVntrCertificate).values(insert_data)
        on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
            **{c.name: c for c in insert_stmt.table.c if c.name != 'id'}
        )
        session.execute(on_duplicate_key_stmt)

    def insert_all_vntr_data(
        self,
        vntr_info: CollectVntrInfoPydantic,
        vntr_finance_balance: List[Optional[CollectVntrFinanceBalancePydantic]],
        vntr_finance_income: List[Optional[CollectVntrFinanceIncomePydantic]],
        vntr_investment: List[Optional[CollectVntrInvestmentInfoPydantic]],
        vntr_certificate: List[Optional[CollectVntrCertificatePydantic]]
    ) -> None:
        """벤처기업 인증번호 정보, 재무정보, 투자정보, 인증정보를 DB에 삽입하는 함수"""
        status = False
        with self.get_session() as session:
            try:
                self.insert_vntr_info(vntr_info, session)
                msg = f'{vntr_info.company_nm}'
                # 리스트가 비어있는 경우에는 삽입하지 않음
                if vntr_finance_balance:
                    self.insert_vntr_finance_balance(vntr_finance_balance, session)
                msg += f', 재무정보 {len(vntr_finance_balance)}개'
                if vntr_finance_income:
                    self.insert_vntr_finance_income(vntr_finance_income, session)
                msg += f', 손익정보 {len(vntr_finance_income)}개'
                if vntr_investment:
                    self.insert_vntr_investment(vntr_investment, session)
                msg += f', 투자정보 {len(vntr_investment)}개'
                if vntr_certificate:
                    self.insert_vntr_certificate(vntr_certificate, session)
                msg += f', 인증정보 {len(vntr_certificate)}개'
                
                status = True
                session.commit()
                msg += '를 DB에 삽입하였습니다.'
                self.logger.info(msg)
            except SQLAlchemyError as e:
                session.rollback()
                msg = traceback.format_exc()
                self.logger.error(f'트랜잭션 에러: {e}\n{msg}')
            except Exception as e:
                session.rollback()
                msg = traceback.format_exc()
                self.logger.error(f'에러: {e}\n{msg}')
            finally:
                session.close()
                return msg, status
