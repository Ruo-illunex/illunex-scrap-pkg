from datetime import date
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, Text, UniqueConstraint
from pydantic import BaseModel

from app.common.db.base import BaseCollections


class CollectVntrFinanceBalance(BaseCollections):
    """벤처기업 재무제표(대차대조표) 모델 클래스"""

    __tablename__ = 'collect_vntr_finance_balance'

    # 테이블 컬럼 정의
    id = Column(Integer, primary_key=True, autoincrement=True, comment='고유번호')
    company_id = Column(Integer, nullable=True, comment='companies.new_company_info.id')
    company_nm = Column(Text, comment='벤처기업 이름')
    corp_no = Column(String(15), comment='법인 번호')
    biz_no = Column(String(10), comment='사업자 번호')
    year = Column(String(4), comment='년도')
    current_assets = Column(String(12), comment='유동자산')
    quick_assets = Column(String(12), comment='당좌자산')
    cash_and_cash_equivalents = Column(String(12), comment='현금및현금성자산')
    short_term_financial_products = Column(String(12), comment='단기금융상품')
    short_term_investment_securities = Column(String(12), comment='단기투자증권')
    short_term_loans = Column(String(12), comment='단기대여금')
    other_short_term_loans = Column(String(12), comment='기타단기대여금')
    trade_receivables = Column(String(12), comment='매출채권')
    prepayments = Column(String(12), comment='선급금')
    other_receivables = Column(String(12), comment='미수금')
    other_current_receivables = Column(String(12), comment='기타미수금')
    advance_expenses = Column(String(12), comment='선급비용')
    other_quick_assets = Column(String(12), comment='기타당좌자산')
    other_unclassified_quick_assets = Column(String(12), comment='기타미분류당좌자산')
    inventory = Column(String(12), comment='재고자산')
    merchandise = Column(String(12), comment='상품')
    products_in_process = Column(String(12), comment='제품')
    half_finished_products = Column(String(12), comment='반제품')
    raw_materials = Column(String(12), comment='원재료')
    supplies = Column(String(12), comment='부재료')
    unfinished_products = Column(String(12), comment='미착제품')
    construction_land = Column(String(12), comment='건설용지')
    completed_buildings = Column(String(12), comment='완공건물')
    unfinished_construction = Column(String(12), comment='미완공건물')
    rental_buildings = Column(String(12), comment='임대주택자산')
    other_inventory = Column(String(12), comment='기타재고자산')
    non_current_assets = Column(String(12), comment='비유동자산')
    investment_assets = Column(String(12), comment='투자자산')
    long_term_financial_products = Column(String(12), comment='장기금융상품')
    long_term_investment_securities = Column(String(12), comment='장기투자증권')
    long_term_loans = Column(String(12), comment='장기대여금')
    related_company_loans = Column(String(12), comment='관계기업대여금')
    executive_and_employee_loans = Column(String(12), comment='임원ㆍ직원대여금')
    other_investment_assets = Column(String(12), comment='기타투자자산')
    tangible_assets = Column(String(12), comment='유형자산')
    land = Column(String(12), comment='토지')
    buildings = Column(String(12), comment='건물')
    structures = Column(String(12), comment='구축물')
    machinery = Column(String(12), comment='기계')
    ships = Column(String(12), comment='선박')
    construction_equipment = Column(String(12), comment='건설장비')
    vehicles = Column(String(12), comment='운송장비')
    equipment = Column(String(12), comment='공구 및 기구')
    construction_in_progress = Column(String(12), comment='공사중인자산')
    other_tangible_assets = Column(String(12), comment='기타유형자산')
    intangible_assets = Column(String(12), comment='무형자산')
    goodwill = Column(String(12), comment='영업권')
    intellectual_property_rights = Column(String(12), comment='산업재산권')
    development_costs = Column(String(12), comment='개발비')
    other_intangible_assets = Column(String(12), comment='기타무형자산')
    other_non_current_assets = Column(String(12), comment='기타비유동자산')
    long_term_receivables = Column(String(12), comment='장기매출채권')
    long_term_prepayments = Column(String(12), comment='장기선급금')
    long_term_unpaid_receivables = Column(String(12), comment='장기미수금')
    rental_deposits = Column(String(12), comment='임대보증금')
    unclassified_other_non_current_assets = Column(String(12), comment='기타미분류비유동자산')
    total_assets = Column(String(12), comment='자산총계')
    current_liabilities = Column(String(12), comment='유동부채')
    short_term_borrowings = Column(String(12), comment='단기차입금')
    trade_payables = Column(String(12), comment='매입채무')
    advanced_receipts = Column(String(12), comment='선수금')
    accrued_expenses = Column(String(12), comment='미지급금')
    deposits_received = Column(String(12), comment='예수금')
    accrued_liabilities = Column(String(12), comment='미지급비용')
    current_portion_of_long_term_liabilities = Column(String(12), comment='유동성장기부채')
    provisions_for_current_liabilities = Column(String(12), comment='유동성부채충당금')
    other_current_liabilities = Column(String(12), comment='기타유동부채')
    non_current_liabilities = Column(String(12), comment='비유동부채')
    long_term_borrowings = Column(String(12), comment='장기차입금')
    special_relationship_long_term_borrowings = Column(String(12), comment='특수관계장기차입금')
    long_term_trade_payables = Column(String(12), comment='장기매입채무')
    long_term_advanced_receipts = Column(String(12), comment='장기선수금')
    long_term_accrued_expenses = Column(String(12), comment='장기미지급금')
    rental_deposits_received = Column(String(12), comment='임대보증금')
    other_guarantee_deposits = Column(String(12), comment='기타보증금')
    provisions_for_retirement_benefits = Column(String(12), comment='퇴직급여충당부채')
    other_provisions = Column(String(12), comment='기타충당부채')
    reserves = Column(String(12), comment='제준비금')
    other_non_current_liabilities = Column(String(12), comment='기타비유동부채')
    total_liabilities = Column(String(12), comment='부채총계')
    capital_stock = Column(String(12), comment='자본금')
    net_income = Column(String(12), comment='당기순손익')
    total_equity = Column(String(12), comment='자본총계')
    total_liabilities_and_equity = Column(String(12), comment='부채와자본총계')
    create_date = Column(Date, default=date.today, comment='생성 날짜')
    update_date = Column(Date, default=date.today, onupdate=date.today, comment='수정일')

    # 인코딩 설정
    __table_args__ = (
        UniqueConstraint('biz_no', 'year', name='uix_biz_no_year'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_general_ci'}
    )


class CollectVntrFinanceBalancePydantic(BaseModel):
    """벤처기업 재무제표 Pydantic 모델"""

    # 모델 필드 정의
    company_id: Optional[int] = None
    company_nm: Optional[str] = None
    corp_no: Optional[str] = None
    biz_no: Optional[str] = None
    year: Optional[str] = None
    current_assets: Optional[str] = None
    quick_assets: Optional[str] = None
    cash_and_cash_equivalents: Optional[str] = None
    short_term_financial_products: Optional[str] = None
    short_term_investment_securities: Optional[str] = None
    short_term_loans: Optional[str] = None
    other_short_term_loans: Optional[str] = None
    trade_receivables: Optional[str] = None
    prepayments: Optional[str] = None
    other_receivables: Optional[str] = None
    other_current_receivables: Optional[str] = None
    advance_expenses: Optional[str] = None
    other_quick_assets: Optional[str] = None
    other_unclassified_quick_assets: Optional[str] = None
    inventory: Optional[str] = None
    merchandise: Optional[str] = None
    products_in_process: Optional[str] = None
    half_finished_products: Optional[str] = None
    raw_materials: Optional[str] = None
    supplies: Optional[str] = None
    unfinished_products: Optional[str] = None
    construction_land: Optional[str] = None
    completed_buildings: Optional[str] = None
    unfinished_construction: Optional[str] = None
    rental_buildings: Optional[str] = None
    other_inventory: Optional[str] = None
    non_current_assets: Optional[str] = None
    investment_assets: Optional[str] = None
    long_term_financial_products: Optional[str] = None
    long_term_investment_securities: Optional[str] = None
    long_term_loans: Optional[str] = None
    related_company_loans: Optional[str] = None
    executive_and_employee_loans: Optional[str] = None
    other_investment_assets: Optional[str] = None
    tangible_assets: Optional[str] = None
    land: Optional[str] = None
    buildings: Optional[str] = None
    structures: Optional[str] = None
    machinery: Optional[str] = None
    ships: Optional[str] = None
    construction_equipment: Optional[str] = None
    vehicles: Optional[str] = None
    equipment: Optional[str] = None
    construction_in_progress: Optional[str] = None
    other_tangible_assets: Optional[str] = None
    intangible_assets: Optional[str] = None
    goodwill: Optional[str] = None
    intellectual_property_rights: Optional[str] = None
    development_costs: Optional[str] = None
    other_intangible_assets: Optional[str] = None
    other_non_current_assets: Optional[str] = None
    long_term_receivables: Optional[str] = None
    long_term_prepayments: Optional[str] = None
    long_term_unpaid_receivables: Optional[str] = None
    rental_deposits: Optional[str] = None
    unclassified_other_non_current_assets: Optional[str] = None
    total_assets: Optional[str] = None
    current_liabilities: Optional[str] = None
    short_term_borrowings: Optional[str] = None
    trade_payables: Optional[str] = None
    advanced_receipts: Optional[str] = None
    accrued_expenses: Optional[str] = None
    deposits_received: Optional[str] = None
    accrued_liabilities: Optional[str] = None
    current_portion_of_long_term_liabilities: Optional[str] = None
    provisions_for_current_liabilities: Optional[str] = None
    other_current_liabilities: Optional[str] = None
    non_current_liabilities: Optional[str] = None
    long_term_borrowings: Optional[str] = None
    special_relationship_long_term_borrowings: Optional[str] = None
    long_term_trade_payables: Optional[str] = None
    long_term_advanced_receipts: Optional[str] = None
    long_term_accrued_expenses: Optional[str] = None
    rental_deposits_received: Optional[str] = None
    other_guarantee_deposits: Optional[str] = None
    provisions_for_retirement_benefits: Optional[str] = None
    other_provisions: Optional[str] = None
    reserves: Optional[str] = None
    other_non_current_liabilities: Optional[str] = None
    total_liabilities: Optional[str] = None
    capital_stock: Optional[str] = None
    net_income: Optional[str] = None
    total_equity: Optional[str] = None
    total_liabilities_and_equity: Optional[str] = None

    class Config:
        from_attributes = True
