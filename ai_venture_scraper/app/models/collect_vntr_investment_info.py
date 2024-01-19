from datetime import date
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, Text, UniqueConstraint
from pydantic import BaseModel

from app.common.db.base import BaseCollections


class CollectVntrInvestmentInfo(BaseCollections):
    """벤처기업 투자정보 모델 클래스"""

    __tablename__ = 'collect_vntr_investment_info'

    # 테이블 컬럼 정의
    id = Column(Integer, primary_key=True, autoincrement=True, comment='고유번호')
    company_id = Column(Integer, nullable=True, comment='companies.new_company_info.id')
    company_nm = Column(Text, comment='벤처기업 이름')
    corp_no = Column(String(15), comment='법인 번호')
    biz_no = Column(String(10), comment='사업자 번호')
    invest_date = Column(String(20), comment='투자 날짜')
    invest_amount = Column(String(20), comment='투자 금액')
    change_amount = Column(String(100), comment='변경사항(잔액)')
    create_date = Column(Date, default=date.today, comment='생성 날짜')
    update_date = Column(Date, default=date.today, onupdate=date.today, comment='수정일')

    # 인코딩 설정
    __table_args__ = (
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


class CollectVntrInvestmentInfoPydantic(BaseModel):
    """벤처기업 투자정보 Pydantic 모델"""

    # 모델 필드 정의
    company_id: Optional[int] = None
    company_nm: Optional[str] = None
    corp_no: Optional[str] = None
    biz_no: Optional[str] = None
    invest_date: Optional[str] = None
    invest_amount: Optional[str] = None
    change_amount: Optional[str] = None

    class Config:
        from_attributes = True
