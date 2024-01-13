from datetime import date
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, UniqueConstraint
from pydantic import BaseModel

from app.common.db.base import BaseCollections


class CollectVntrFinanceIncome(BaseCollections):
    """벤처기업 재무제표(손익계산서) 정보 모델 클래스"""

    __tablename__ = 'collect_vntr_finance_income'

    # 테이블 컬럼 정의
    id = Column(Integer, primary_key=True, autoincrement=True, comment='고유번호')
    company_id = Column(Integer, nullable=True, comment='companies.new_company_info.id')
    company_nm = Column(String(20), comment='벤처기업 이름')
    corp_no = Column(String(15), comment='법인 번호')
    biz_no = Column(String(10), comment='사업자 번호')
    year = Column(String(4), comment='년도')
    total_revenue = Column(String(12), comment='매출액')
    goods_sales = Column(String(12), comment='상품매출')
    product_sales = Column(String(12), comment='제품매출')
    construction_revenue = Column(String(12), comment='공사수익')
    real_estate_sales = Column(String(12), comment='분양수입')
    rental_income = Column(String(12), comment='임대수익')
    service_income = Column(String(12), comment='서비스수입')
    other_revenue = Column(String(12), comment='기타매출')
    cost_of_sales = Column(String(12), comment='매출원가')
    goods_cost_of_sales = Column(String(12), comment='상품매출원가')
    opening_inventory = Column(String(12), comment='기초재고')
    purchases = Column(String(12), comment='당기매입액')
    closing_inventory = Column(String(12), comment='기말재고')
    other_account_transfers = Column(String(12), comment='타계정대체')
    other_cost_of_sales = Column(String(12), comment='기타매출원가')
    manufacturing_construction_costs = Column(String(12), comment='제조공사비')
    other_costs = Column(String(12), comment='기타원가')
    gross_profit = Column(String(12), comment='매출총이익')
    selling_and_admin_expenses = Column(String(12), comment='판매비와관리비')
    salaries_and_wages = Column(String(12), comment='급여')
    day_wages = Column(String(12), comment='일용직급여')
    retirement_benefit_costs = Column(String(12), comment='퇴직급여')
    welfare_expenses = Column(String(12), comment='복리후생비')
    travel_and_transportation = Column(String(12), comment='여비교통비')
    rental_expenses = Column(String(12), comment='임차료')
    communication_expenses = Column(String(12), comment='통신비')
    electricity_expenses = Column(String(12), comment='전기비')
    water_and_heating_expenses = Column(String(12), comment='수도비')
    fuel_costs = Column(String(12), comment='연료비')
    insurance_premiums = Column(String(12), comment='보험료')
    lease_expenses = Column(String(12), comment='리스료')
    taxes_and_duties = Column(String(12), comment='세금과공과')
    depreciation = Column(String(12), comment='감가상각비')
    amortization_of_intangible_assets = Column(String(12), comment='무형자산상각비')
    repair_costs = Column(String(12), comment='수선비')
    building_management_fees = Column(String(12), comment='건물관리비')
    entertainment_expenses = Column(String(12), comment='접대비')
    advertising_and_promotion = Column(String(12), comment='광고선전비')
    printing_and_stationery = Column(String(12), comment='인쇄.문구비')
    transportation_costs = Column(String(12), comment='운반비')
    vehicle_maintenance = Column(String(12), comment='차량유지비')
    training_expenses = Column(String(12), comment='교육훈련비')
    commission_fees = Column(String(12), comment='지급수수료')
    sales_commissions = Column(String(12), comment='판매수수료')
    bad_debt_expenses = Column(String(12), comment='대손충당금')
    research_and_development = Column(String(12), comment='경상개발비')
    supplies_expenses = Column(String(12), comment='소모품비')
    management_service_fees = Column(String(12), comment='경영자문료')
    service_costs = Column(String(12), comment='용역비')
    other_expenses_subtotal = Column(String(12), comment='기타비용소계')
    operating_income = Column(String(12), comment='영업손익')
    non_operating_income = Column(String(12), comment='영업외수익')
    interest_income = Column(String(12), comment='이자수익')
    dividend_income = Column(String(12), comment='배당금수익')
    foreign_exchange_gains = Column(String(12), comment='외환차익')
    foreign_currency_translation_gains = Column(String(12), comment='외화환산이익')
    gain_on_disposal_of_short_term_investments = Column(String(12), comment='단기투자자산처분이익')
    gain_on_disposal_of_investment_assets = Column(String(12), comment='투자자산처분이익')
    gain_on_disposal_of_tangible_and_intangible_assets = Column(String(12), comment='유형무형자산처분이익')
    insurance_recovery = Column(String(12), comment='보험차익')
    reversal_of_provisions = Column(String(12), comment='충당금준비금환입')
    correction_of_prior_period_errors_gain = Column(String(12), comment='이전년도오류정정이익')
    other_non_operating_income_subtotal = Column(String(12), comment='기타영업외수익소계')
    non_operating_expenses = Column(String(12), comment='영업외비용')
    interest_expenses = Column(String(12), comment='이자비용')
    foreign_exchange_losses = Column(String(12), comment='외환차손')
    foreign_currency_translation_losses = Column(String(12), comment='외화환산손실')
    bad_debt_expenses_investment_assets = Column(String(12), comment='기타대손상각비(총당금전입액포함)')
    donations = Column(String(12), comment='기부금')
    loss_on_disposal_of_short_term_investments = Column(String(12), comment='단기투자자산처분손실')
    loss_on_disposal_of_investment_assets = Column(String(12), comment='투자자산처분손실')
    loss_on_disposal_of_tangible_and_intangible_assets = Column(String(12), comment='유형무형자산처분손실')
    inventory_write_off_losses = Column(String(12), comment='재고차손')
    losses_due_to_disasters = Column(String(12), comment='재해손실')
    provision_expenses = Column(String(12), comment='충당금준비금전입')
    correction_of_prior_period_errors_loss = Column(String(12), comment='이전년도오류정정손실')
    other_non_operating_expenses_subtotal = Column(String(12), comment='기타영업외비용소계')
    net_income = Column(String(12), comment='당기순손익')
    create_date = Column(Date, default=date.today, comment='생성 날짜')
    update_date = Column(Date, default=date.today, onupdate=date.today, comment='수정일')


    # 인코딩 설정
    __table_args__ = (
        UniqueConstraint('biz_no', 'year', name='uix_biz_no_year'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


class CollectVntrFinanceIncomePydantic(BaseModel):
    """벤처기업 재무제표(손익계산서) 정보 Pydantic 모델"""

    # 모델 필드 정의
    company_id: Optional[int] = None
    company_nm: Optional[str] = None
    corp_no: Optional[str] = None
    biz_no: Optional[str] = None
    year: Optional[str] = None
    total_revenue: Optional[str] = None
    goods_sales: Optional[str] = None
    product_sales: Optional[str] = None
    construction_revenue: Optional[str] = None
    real_estate_sales: Optional[str] = None
    rental_income: Optional[str] = None
    service_income: Optional[str] = None
    other_revenue: Optional[str] = None
    cost_of_sales: Optional[str] = None
    goods_cost_of_sales: Optional[str] = None
    opening_inventory: Optional[str] = None
    purchases: Optional[str] = None
    closing_inventory: Optional[str] = None
    other_account_transfers: Optional[str] = None
    other_cost_of_sales: Optional[str] = None
    manufacturing_construction_costs: Optional[str] = None
    other_costs: Optional[str] = None
    gross_profit: Optional[str] = None
    selling_and_admin_expenses: Optional[str] = None
    salaries_and_wages: Optional[str] = None
    day_wages: Optional[str] = None
    retirement_benefit_costs: Optional[str] = None
    welfare_expenses: Optional[str] = None
    travel_and_transportation: Optional[str] = None
    rental_expenses: Optional[str] = None
    communication_expenses: Optional[str] = None
    electricity_expenses: Optional[str] = None
    water_and_heating_expenses: Optional[str] = None
    fuel_costs: Optional[str] = None
    insurance_premiums: Optional[str] = None
    lease_expenses: Optional[str] = None
    taxes_and_duties: Optional[str] = None
    depreciation: Optional[str] = None
    amortization_of_intangible_assets: Optional[str] = None
    repair_costs: Optional[str] = None
    building_management_fees: Optional[str] = None
    entertainment_expenses: Optional[str] = None
    advertising_and_promotion: Optional[str] = None
    printing_and_stationery: Optional[str] = None
    transportation_costs: Optional[str] = None
    vehicle_maintenance: Optional[str] = None
    training_expenses: Optional[str] = None
    commission_fees: Optional[str] = None
    sales_commissions: Optional[str] = None
    bad_debt_expenses: Optional[str] = None
    research_and_development: Optional[str] = None
    supplies_expenses: Optional[str] = None
    management_service_fees: Optional[str] = None
    service_costs: Optional[str] = None
    other_expenses_subtotal: Optional[str] = None
    operating_income: Optional[str] = None
    non_operating_income: Optional[str] = None
    interest_income: Optional[str] = None
    dividend_income: Optional[str] = None
    foreign_exchange_gains: Optional[str] = None
    foreign_currency_translation_gains: Optional[str] = None
    gain_on_disposal_of_short_term_investments: Optional[str] = None
    gain_on_disposal_of_investment_assets: Optional[str] = None
    gain_on_disposal_of_tangible_and_intangible_assets: Optional[str] = None
    insurance_recovery: Optional[str] = None
    reversal_of_provisions: Optional[str] = None
    correction_of_prior_period_errors_gain: Optional[str] = None
    other_non_operating_income_subtotal: Optional[str] = None
    non_operating_expenses: Optional[str] = None
    interest_expenses: Optional[str] = None
    foreign_exchange_losses: Optional[str] = None
    foreign_currency_translation_losses: Optional[str] = None
    bad_debt_expenses_investment_assets: Optional[str] = None
    donations: Optional[str] = None
    loss_on_disposal_of_short_term_investments: Optional[str] = None
    loss_on_disposal_of_investment_assets: Optional[str] = None
    loss_on_disposal_of_tangible_and_intangible_assets: Optional[str] = None
    inventory_write_off_losses: Optional[str] = None
    losses_due_to_disasters: Optional[str] = None
    provision_expenses: Optional[str] = None
    correction_of_prior_period_errors_loss: Optional[str] = None
    other_non_operating_expenses_subtotal: Optional[str] = None
    net_income: Optional[str] = None

    class Config:
        from_attributes = True
