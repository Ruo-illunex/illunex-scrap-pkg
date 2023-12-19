from datetime import date

from sqlalchemy import Column, String, Integer, Date, ForeignKey
from pydantic import BaseModel

from app.common.db.base import BaseCompanies


class NewScrapCompanyDartInfo(BaseCompanies):
    """DART 기업 정보 모델 클래스"""

    __tablename__ = 'new_scrap_company_dart_info'

    # 테이블 컬럼 정의
    scrap_id = Column(Integer, primary_key=True, autoincrement=True, comment='고유번호')
    company_id = Column(Integer, ForeignKey('new_scrap_company.id'), nullable=False, comment='new_scrap_company.id')
    origin_id = Column(Integer, comment='dart: 16, 2016 -> coex')
    company_name = Column(String(255), comment='기업명')
    biz_num = Column(String(13), comment='사업자등록번호')
    corporation_num = Column(String(13), comment='법인등록번호')
    real_company_name = Column(String(255), comment='순수 기업명')
    representation_name = Column(String(60), comment='대표자명')
    listing_market_id = Column(String(3), comment='상장시장구분코드')
    listing_market_desc = Column(String(10), comment='상장코드명')
    address = Column(String(255), comment='주소')
    homepage = Column(String(255), comment='홈페이지 주소')
    tel = Column(String(50), comment='전화번호')
    fax = Column(String(20), comment='팩스')
    business_condition_code = Column(String(1), default='', comment='산업코드 업태 알파벳')
    business_condition_desc = Column(String(255), default='', comment='산업코드 업태명')
    business_category_code = Column(String(10), comment='산업코드')
    business_category_desc = Column(String(255), comment='산업코드명')
    establishment_date = Column(String(20), comment='설립일')
    acct_month = Column(String(50), comment='재무일자')
    create_date = Column(Date, comment='생성일')
    update_date = Column(Date, comment='수정일')

    # 인코딩 설정
    __table_args__ = {
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }


class NewScrapCompanyDartInfoPydantic(BaseModel):
    """DART 기업 정보 Pydantic 모델"""

    # 모델 필드 정의
    company_id: int
    origin_id: int
    company_name: str
    biz_num: str
    corporation_num: str
    real_company_name: str
    representation_name: str
    listing_market_id: str
    listing_market_desc: str
    address: str
    homepage: str
    tel: str
    fax: str
    business_condition_code: str
    business_condition_desc: str
    business_category_code: str
    business_category_desc: str
    establishment_date: str
    acct_month: str
    create_date: date
    update_date: date

    class Config:
        from_attributes = True
