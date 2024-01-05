from datetime import date
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, Text
from pydantic import BaseModel

from app.common.db.base import BaseCollections


class CollectDartNotice(BaseCollections):
    """DART에서 수집한 공시 정보 모델 클래스"""
    
    __tablename__ = 'collect_dart_notice'
    
    # 테이블 컬럼 정의
    id = Column(Integer, primary_key=True, autoincrement=True, comment='고유번호')
    company_id = Column(Integer, nullable=True, comment='companies.new_company_info.id')
    corp_cls = Column(String(10), comment='법인 분류')
    corp_name = Column(String(100), comment='법인 이름')
    corp_code = Column(String(100), comment='DART 고유번호')
    stock_code = Column(String(100), comment='종목 코드')
    report_nm = Column(String(200), comment='보고서 이름')
    rcept_no = Column(String(100), unique=True, comment='접수 번호')
    flr_nm = Column(String(100), comment='공시 제출인 이름')
    rcept_dt = Column(String(50), comment='접수 날짜')
    rm = Column(Text, comment='비고')
    create_date = Column(Date, default=date.today, comment='생성 날짜')
    update_date = Column(Date, default=date.today, onupdate=date.today, comment='수정일')
    
    # 인코딩 설정
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }


class CollectDartNoticePydantic(BaseModel):
    """DART에서 수집한 공시 정보 Pydantic 모델"""
    
    # 모델 필드 정의
    company_id: Optional[int] = None
    corp_cls: Optional[str] = None
    corp_name: Optional[str] = None
    corp_code: Optional[str] = None
    stock_code: Optional[str] = None
    report_nm: Optional[str] = None
    rcept_no: Optional[str] = None
    flr_nm: Optional[str] = None
    rcept_dt: Optional[str] = None
    rm: Optional[str] = None
    
    class Config:
        from_attributes = True
