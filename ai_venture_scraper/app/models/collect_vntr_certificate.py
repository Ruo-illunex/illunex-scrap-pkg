from datetime import date
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, UniqueConstraint
from pydantic import BaseModel

from app.common.db.base import BaseCollections


class CollectVntrCertificate(BaseCollections):
    """벤처기업 인증번호 정보 모델 클래스"""

    __tablename__ = 'collect_vntr_certificate'

    # 테이블 컬럼 정의
    id = Column(Integer, primary_key=True, autoincrement=True, comment='고유번호')
    company_id = Column(Integer, nullable=True, comment='companies.new_company_info.id')
    company_nm = Column(String(20), comment='벤처기업 이름')
    corp_no = Column(String(15), comment='법인 번호')
    biz_no = Column(String(10), comment='사업자 번호')
    certificate_no = Column(String(5), comment='인증순서')
    certificate_type = Column(String(30), comment='벤처기업확인서 유형')
    announcement_date = Column(String(12), comment='공시일')
    validity_period = Column(String(30), comment='유효기간')
    certificate_number = Column(String(30), comment='벤처확인번호')
    certificate_date = Column(String(12), comment='최초확인일')
    changes = Column(String(100), comment='변경사항')
    create_date = Column(Date, default=date.today, comment='생성 날짜')
    update_date = Column(Date, default=date.today, onupdate=date.today, comment='수정일')

    # 인코딩 설정
    __table_args__ = (
        UniqueConstraint('biz_no', 'certificate_number', name='uix_biz_no_certificate_number'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


class CollectVntrCertificatePydantic(BaseModel):
    """벤처기업 인증번호 정보 Pydantic 모델"""

    # 모델 필드 정의
    company_id: Optional[int] = None
    company_nm: Optional[str] = None
    corp_no: Optional[str] = None
    biz_no: Optional[str] = None
    certificate_no: Optional[str] = None
    certificate_type: Optional[str] = None
    announcement_date: Optional[str] = None
    validity_period: Optional[str] = None
    certificate_number: Optional[str] = None
    certificate_date: Optional[str] = None
    changes: Optional[str] = None

    class Config:
        from_attributes = True
