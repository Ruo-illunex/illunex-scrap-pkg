from datetime import date
from typing import Optional

from sqlalchemy import Column, Integer, String, Date
from pydantic import BaseModel

from app.common.db.base import BaseCollections


class CollectVntrInfo(BaseCollections):
    """벤처기업 인증번호 정보 모델 클래스"""

    __tablename__ = 'collect_vntr_info'

    # 테이블 컬럼 정의
    id = Column(Integer, primary_key=True, autoincrement=True, comment='고유번호')
    company_id = Column(Integer, nullable=True, comment='companies.new_company_info.id')
    company_nm = Column(String(30), comment='벤처기업 이름')
    representative_nm = Column(String(20), comment='대표자 이름')
    corp_no = Column(String(50), comment='법인 번호')
    indsty_cd = Column(String(10), comment='업종코드')
    indsty_nm = Column(String(50), comment='업종명')
    main_prod = Column(String(50), comment='주요제품')
    biz_no = Column(String(50), unique=True, comment='사업자 번호')
    tel_no = Column(String(50), comment='전화 번호')
    address = Column(String(200), comment='주소')
    create_date = Column(Date, default=date.today, comment='생성 날짜')
    update_date = Column(Date, default=date.today, onupdate=date.today, comment='수정일')

    # 인코딩 설정
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }


class CollectVntrInfoPydantic(BaseModel):
    """벤처기업 인증번호 정보 Pydantic 모델"""

    # 모델 필드 정의
    company_id: Optional[int] = None
    company_nm: Optional[str] = None
    representative_nm: Optional[str] = None
    corp_no: Optional[str] = None
    indsty_cd: Optional[str] = None
    indsty_nm: Optional[str] = None
    main_prod: Optional[str] = None
    biz_no: Optional[str] = None
    tel_no: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True
