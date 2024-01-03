from datetime import date
from typing import Optional

from sqlalchemy import Column, Integer, String, BigInteger, Date, inspect
from pydantic import BaseModel

from app.common.db.base import BaseCollections


class CollectDartFinance(BaseCollections):
    """DART에서 수집한 재무 정보 모델 클래스"""

    __tablename__ = 'collect_dart_finance'

    # 테이블 컬럼 정의
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='고유번호')
    company_id = Column(Integer, nullable=True, comment='companies.new_company_info.id')
    rcept_no = Column(String(20), comment='접수번호')
    reprt_code = Column(String(5), comment='보고서 코드')
    bsns_year = Column(String(5), comment='사업 연도')
    corp_code = Column(String(10), comment='고유번호')
    fs_div = Column(String(5), comment='개별/연결구분')
    fs_nm = Column(String(100), comment='개별/연결명')
    sj_div = Column(String(10), comment='재무제표 구분')
    sj_nm = Column(String(100), comment='재무제표 명')
    account_id = Column(String(1000), comment='계정ID')
    account_nm = Column(String(255), comment='계정명')
    account_detail = Column(String(255), nullable=True, comment='계정상세')
    thstrm_nm = Column(String(45), nullable=True, comment='당기명')
    thstrm_amount = Column(String(100), nullable=True, comment='당기금액')
    thstrm_add_amount = Column(String(100), nullable=True, comment='당기누적금액')
    frmtrm_nm = Column(String(45), nullable=True, comment='전기명')
    frmtrm_amount = Column(String(100), nullable=True, comment='전기금액')
    frmtrm_q_nm = Column(String(45), nullable=True, comment='전기분기명')
    frmtrm_q_amount = Column(String(100), nullable=True, comment='전기분기금액')
    frmtrm_add_amount = Column(String(100), nullable=True, comment='전기누적금액')
    bfefrmtrm_nm = Column(String(45), nullable=True, comment='전전기명')
    bfefrmtrm_amount = Column(String(100), nullable=True, comment='전전기금액')
    ord = Column(String(10), comment='계정정렬순서')
    currency = Column(String(10), comment='통화 단위')
    create_date = Column(Date, default=date.today, comment='생성 날짜')
    update_date = Column(Date, default=date.today, onupdate=date.today, comment='수정일')


    # 인코딩 설정
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }
    
    def to_dict(self):
        """모델 인스턴스를 딕셔너리로 변환하는 메서드"""
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class CollectDartFinancePydantic(BaseModel):
    """DART에서 수집한 재무 정보 Pydantic 모델"""

    # 모델 필드 정의
    company_id: Optional[int] = None
    rcept_no: Optional[str] = ''
    reprt_code: Optional[str] = ''
    bsns_year: Optional[str] = ''
    corp_code: Optional[str] = ''
    fs_div: Optional[str] = ''
    fs_nm: Optional[str] = ''
    sj_div: Optional[str] = ''
    sj_nm: Optional[str] = ''
    account_id: Optional[str] = ''
    account_nm: Optional[str] = ''
    account_detail: Optional[str] = ''
    thstrm_nm: Optional[str] = ''
    thstrm_amount: Optional[str] = ''
    thstrm_add_amount: Optional[str] = ''
    frmtrm_nm: Optional[str] = ''
    frmtrm_amount: Optional[str] = ''
    frmtrm_q_nm: Optional[str] = ''
    frmtrm_q_amount: Optional[str] = ''
    frmtrm_add_amount: Optional[str] = ''
    bfefrmtrm_nm: Optional[str] = ''
    bfefrmtrm_amount: Optional[str] = ''
    ord: Optional[str] = ''
    currency: Optional[str] = ''

    class Config:
        from_attributes = True
