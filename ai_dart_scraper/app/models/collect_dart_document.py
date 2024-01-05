from datetime import date
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, Text
from pydantic import BaseModel

from app.common.db.base import BaseCollections


class CollectDartDocument(BaseCollections):
    """DART에서 수집한 공시 서류 원본 모델 클래스"""
    
    __tablename__ = 'collect_dart_document'
    
    # 테이블 컬럼 정의
    id = Column(Integer, primary_key=True, autoincrement=True, comment='고유번호')
    company_id = Column(Integer, nullable=True, comment='companies.new_company_info.id')
    rcept_no = Column(String(100), comment='접수 번호')
    document = Column(Text, comment='공시 서류 원본')
    create_date = Column(Date, default=date.today, comment='생성 날짜')
    update_date = Column(Date, default=date.today, onupdate=date.today, comment='수정일')
    
    # 인코딩 설정
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }


class CollectDartDocumentPydantic(BaseModel):
    """DART에서 수집한 공시 서류 원본 Pydantic 모델"""
    
    # 모델 필드 정의
    company_id: Optional[int] = None
    rcept_no: Optional[str] = None
    document: Optional[str] = None
    create_date: Optional[date] = None
    update_date: Optional[date] = None
    
    class Config:
        from_attributes = True
