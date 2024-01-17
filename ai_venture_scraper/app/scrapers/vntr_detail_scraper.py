import time
import traceback
from typing import Optional, Tuple, List
from collections import deque
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from app.config.settings import FILE_PATHS, TROCR_API_TOKEN
from app.common.core.utils import make_dir, get_current_datetime
from app.common.log.log_config import setup_logger
from app.scrapers.vntr_list_scraper import VntrListScraper
from app.database_init import collections_db, companies_db
from app.models_init import (
    CollectVntrInfoPydantic,
    CollectVntrFinanceBalancePydantic,
    CollectVntrFinanceIncomePydantic,
    CollectVntrInvestmentInfoPydantic,
    CollectVntrCertificatePydantic,
)


class VntrScraper:
    def __init__(self) -> None:
        self._data_path = FILE_PATHS['data']
        self._log_path = FILE_PATHS['log'] + 'vntr_scraper'

        make_dir(self._log_path)
        self._log_file = self._log_path + f'/{get_current_datetime()}.log'
        self._logger = setup_logger(
            'vntr_scraper',
            self._log_file
        )

        self.captcha_url = "https://www.smes.go.kr/venturein/pbntc/captchaImg.do"
        self._api_url = "https://api-inference.huggingface.co/models/microsoft/trocr-base-printed"
        self._api_headers = {"Authorization": f"Bearer {TROCR_API_TOKEN}"}

        self._comp_id_df = companies_db.get_company_id_df()
        self._init_data()

    def _init_data(self) -> None:
        """데이터를 초기화하는 함수
        """
        self.company_info = {
            'company_id': None,
            'company_nm': None,
            'representative_nm': None,
            'corp_no': None,
            'indsty_cd': None,
            'indsty_nm': None,
            'main_prod': None,
            'biz_no': None,
            'tel_no': None,
            'address': None,
        }
        self.company_finance = {
            'company_id': None,
            'company_nm': None,
            'corp_no': None,
            'biz_no': None,
            'balance_sheet': [],    # 재무상태표
            'income_statement': [],     # 손익계산서
        }
        self.investment_info = {
            'company_id': None,
            'company_nm': None,
            'corp_no': None,
            'biz_no': None,
            'investment_details': [],  # 투자정보 상세정보
        }
        self.venture_business_certificate = {
            'company_id': None,
            'company_nm': None,
            'corp_no': None,
            'biz_no': None,
            'certificate_details': [],  # 벤처기업확인서 상세정보
        }

    def _get_vntr_list(self) -> Optional[dict]:
        """벤처기업 인증번호 목록을 가져오는 함수

        Returns:
            Optional[dict]: 벤처기업 인증번호 목록 (key: 벤처기업 인증번호, value: 산업코드)
        """
        try:
            vntr_list_scraper = VntrListScraper()
            self._vntr_dict = vntr_list_scraper.read_vntr_sn_indstycd_dict()
            if self._vntr_dict is None:
                self._logger.error('벤처기업 인증번호 목록을 다시 가져옵니다.')
                print('벤처기업 인증번호 목록을 다시 가져옵니다.')
                return self._get_vntr_list()
            vntr_list = list(self._vntr_dict.keys())
            return vntr_list
        except Exception as e:
            self._logger.error(f'벤처기업 인증번호 목록을 가져오는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def _get_driver(self, url: str) -> Optional[webdriver.Chrome]:
        """ChromeDriver를 가져오는 함수

        Args:
            url (str): 접속할 URL

        Returns:
            webdriver.Chrome: ChromeDriver
        """
        try:
            self._logger.info('ChromeDriver를 가져옵니다.')
            print('ChromeDriver를 가져옵니다.')
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(
                options=chrome_options
                )
            driver.get(url)
            return driver
        except Exception as e:
            self._logger.error(f'ChromeDriver를 가져오는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def _get_captcha_key(self, driver: webdriver.Chrome) -> Optional[str]:
        """캡챠 키를 가져오는 함수

        Args:
            driver (webdriver.Chrome): ChromeDriver

        Returns:
            Optional[str]: 캡챠 키
        """
        file_path = self._data_path + 'captcha.png'
        try:
            self._logger.info(f'캡챠 키를 가져옵니다.')
            print(f'캡챠 키를 가져옵니다.')
            # 새로고침
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "img")))
            # 이미지 요소를 찾아서 우클릭 후 이미지 저장
            driver.find_element(By.TAG_NAME, "img").screenshot(file_path)
            with open(file_path, "rb") as f:
                img_data = f.read()
            # TROCR API 요청
            response = requests.post(
                self._api_url, headers=self._api_headers, data=img_data
                )
            output = response.json()
            captcha_key = output[0]["generated_text"]
            self._logger.info(f'캡챠 키: {captcha_key}')
            print(f'캡챠 키: {captcha_key}')
            return captcha_key
        except Exception as e:
            self._logger.error(f'캡챠 키를 가져오는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def _preprocess_digit_value(self, value: str) -> str:
        """숫자로 이루어진 문자열을 전처리하는 함수

        Args:
            value (str): 전처리할 문자열

        Returns:
            str: 전처리된 문자열
        """
        if value in ['0', '']:
            return value
        return ''.join(value.split(',')[:-1])

    def _get_financial_info(self, driver: webdriver.Chrome, xpath: str) -> list:
        """재무정보를 가져오는 함수

        Args:
            driver (webdriver.Chrome): ChromeDriver
            xpath (str): xpath

        Returns:
            list: 재무정보
        """
        row = driver.find_elements(By.XPATH, xpath)
        data = [item.text for item in row]
        return data

    def _get_balance_sheet(self, data: tuple) -> dict:
        data = list(data)
        data[1:] = list(map(self._preprocess_digit_value, data[1:]))
        return {
            'year': data[0],  # 년도
            'current_assets': data[1],  # 유동자산 총계
            'quick_assets': data[2],  # 당좌자산 총계
            'cash_and_cash_equivalents': data[3],  # 현금 및 현금성자산
            'short_term_financial_products': data[4],  # 단기금융상품
            'short_term_investment_securities': data[5],  # 단기투자증권
            'short_term_loans': data[6],  # 단기대여금
            'other_short_term_loans': data[7],  # 기타단기대여금
            'trade_receivables': data[8],  # 매출채권
            'prepayments': data[9],  # 선급금
            'other_receivables': data[10],  # 미수금
            'other_current_receivables': data[11],  # 기타미수금
            'advance_expenses': data[12],  # 선급비용
            'other_quick_assets': data[13],  # 기타당좌자산
            'other_unclassified_quick_assets': data[14],  # 기타미분류당좌자산
            'inventory': data[15],  # 재고자산
            'merchandise': data[16],  # 상품
            'products_in_process': data[17],  # 제품
            'half_finished_products': data[18],  # 반제품 및 재공품
            'raw_materials': data[19],  # 원재료
            'supplies': data[20],  # 부재료
            'unfinished_products': data[21],  # 미착제품
            'construction_land': data[22],  # 건설용지
            'completed_buildings': data[23],  # 완성건물
            'unfinished_construction': data[24],  # 미완성공사
            'rental_buildings': data[25],  # 임대주택자산
            'other_inventory': data[26],  # 기타 재고자산
            'non_current_assets': data[27],  # 비유동자산 총계
            'investment_assets': data[28],  # 투자자산
            'long_term_financial_products': data[29],  # 장기금융상품
            'long_term_investment_securities': data[30],  # 장기투자증권
            'long_term_loans': data[31],  # 장기대여금
            'related_company_loans': data[32],  # 관계회사대여금
            'executive_and_employee_loans': data[33],  # 임원 및 종업원 대여금
            'other_investment_assets': data[34],  # 기타 투자자산
            'tangible_assets': data[35],  # 유형자산
            'land': data[36],  # 토지
            'buildings': data[37],  # 건물
            'structures': data[38],  # 구축물
            'machinery': data[39],  # 기계장치
            'ships': data[40],  # 선박
            'construction_equipment': data[41],  # 건설장비
            'vehicles': data[42],  # 차량운반구
            'equipment': data[43],  # 공구 및 기구
            'construction_in_progress': data[44],  # 건설중인자산
            'other_tangible_assets': data[45],  # 기타 유형자산
            'intangible_assets': data[46],  # 무형자산
            'goodwill': data[47],  # 영업권
            'intellectual_property_rights': data[48],  # 산업재산권
            'development_costs': data[49],  # 개발비
            'other_intangible_assets': data[50],  # 기타 무형자산
            'other_non_current_assets': data[51],  # 기타 비유동자산
            'long_term_receivables': data[52],  # 장기매출채권
            'long_term_prepayments': data[53],  # 장기선급금
            'long_term_unpaid_receivables': data[54],  # 장기미수금
            'rental_deposits': data[55],  # 임차보증금
            'unclassified_other_non_current_assets': data[56],  # 기타 미분류 비유동자산
            'total_assets': data[57],  # 자산총계
            'current_liabilities': data[58],  # 유동부채
            'short_term_borrowings': data[59],  # 단기차입금
            'trade_payables': data[60],  # 매입채무
            'advanced_receipts': data[61],  # 선수금
            'accrued_expenses': data[62],  # 미지급금
            'deposits_received': data[63],  # 예수금
            'accrued_liabilities': data[64],  # 미지급비용
            'current_portion_of_long_term_liabilities': data[65],  # 유동성장기부채
            'provisions_for_current_liabilities': data[66],  # 유동성충당부채
            'other_current_liabilities': data[67],  # 기타 유동부채
            'non_current_liabilities': data[68],  # 비유동부채
            'long_term_borrowings': data[69],  # 장기차입금
            'special_relationship_long_term_borrowings': data[70],  # 특수관계자장기차입금
            'long_term_trade_payables': data[71],  # 장기매입채무
            'long_term_advanced_receipts': data[72],  # 장기선수금
            'long_term_accrued_expenses': data[73],  # 장기미지급금
            'rental_deposits_received': data[74],  # 임대보증금
            'other_guarantee_deposits': data[75],  # 기타보증금
            'provisions_for_retirement_benefits': data[76],  # 퇴직급여충당부채
            'other_provisions': data[77],  # 기타충당부채
            'reserves': data[78],  # 제준비금
            'other_non_current_liabilities': data[79],  # 기타 비유동부채
            'total_liabilities': data[80],  # 부채총계
            'capital_stock': data[81],  # 자본금
            'net_income': data[82],  # 당기순손익
            'total_equity': data[83],  # 자본총계
            'total_liabilities_and_equity': data[84],  # 부채 및 자본총계
        }

    def _get_income_statement(self, data: tuple) -> dict:
        data = list(data)
        data[1:] = list(map(self._preprocess_digit_value, data[1:]))
        return {
            'year': data[0],  # 년도
            'total_revenue': data[1],  # 매출액 총계
            'goods_sales': data[2],  # 상품매출
            'product_sales': data[3],  # 제품매출
            'construction_revenue': data[4],  # 공사수입
            'real_estate_sales': data[5],  # 분양수입
            'rental_income': data[6],  # 임대수입
            'service_income': data[7],  # 서비스수입
            'other_revenue': data[8],  # 기타 매출
            'cost_of_sales': data[9],  # 매출원가
            'goods_cost_of_sales': data[10],  # 상품매출원가
            'opening_inventory': data[11],  # 기초재고액
            'purchases': data[12],  # 당기매입액
            'closing_inventory': data[13],  # 기말재고액
            'other_account_transfers': data[14],  # 타계정대체액
            'other_cost_of_sales': data[15],  # 기타 매출원가
            'manufacturing_construction_costs': data[16],  # 제조·공사·분양
            'other_costs': data[17],  # 기타원가
            'gross_profit': data[18],  # 매출총이익 (매출액 - 매출원가)
            'selling_and_admin_expenses': data[19],  # 판매비와 관리비
            'salaries_and_wages': data[20],  # 급여와 임금·제수당
            'day_wages': data[21],  # 일용급여
            'retirement_benefit_costs': data[22],  # 퇴직급여(충당부채 전입·환입액 포함)
            'welfare_expenses': data[23],  # 복리후생비
            'travel_and_transportation': data[24],  # 여비교통비
            'rental_expenses': data[25],  # 임차료
            'communication_expenses': data[26],  # 통신비
            'electricity_expenses': data[27],  # 전력비
            'water_and_heating_expenses': data[28],  # 수도광열비
            'fuel_costs': data[29],  # 유류비
            'insurance_premiums': data[30],  # 보험료
            'lease_expenses': data[31],  # 리스료
            'taxes_and_duties': data[32],  # 세금과공과
            'depreciation': data[33],  # 감가상각비
            'amortization_of_intangible_assets': data[34],  # 무형자산상각비
            'repair_costs': data[35],  # 수선비
            'building_management_fees': data[36],  # 건물관리비
            'entertainment_expenses': data[37],  # 접대비
            'advertising_and_promotion': data[38],  # 광고선전비
            'printing_and_stationery': data[39],  # 도서인쇄비
            'transportation_costs': data[40],  # 운반비
            'vehicle_maintenance': data[41],  # 차량유지비
            'training_expenses': data[42],  # 교육훈련비
            'commission_fees': data[43],  # 지급수수료
            'sales_commissions': data[44],  # 판매수수료
            'bad_debt_expenses': data[45],  # 대손상각비(충당금 전입·환입액 포함)
            'research_and_development': data[46],  # 경상개발비
            'supplies_expenses': data[47],  # 소모품비
            'management_service_fees': data[48],  # 경영위탁수수료(프랜차이즈 수수료 포함)
            'service_costs': data[49],  # 용역비
            'other_expenses_subtotal': data[50],  # 기타소계
            'operating_income': data[51],  # 영업손익 (매출총이익 - 판매비와 관리비)
            'non_operating_income': data[52],  # 영업외수익
            'interest_income': data[53],  # 이자수익
            'dividend_income': data[54],  # 배당금수익
            'foreign_exchange_gains': data[55],  # 외환차익
            'foreign_currency_translation_gains': data[56],  # 외화환산이익
            'gain_on_disposal_of_short_term_investments': data[57],  # 단기투자자산 처분이익
            'gain_on_disposal_of_investment_assets': data[58],  # 투자자산 처분이익
            'gain_on_disposal_of_tangible_and_intangible_assets': data[59],  # 유·무형자산 처분이익
            'insurance_recovery': data[60],  # 보험차익
            'reversal_of_provisions': data[61],  # 충당금·준비금 환입액
            'correction_of_prior_period_errors_gain': data[62],  # 전기오류수정이익
            'other_non_operating_income_subtotal': data[63],  # 기타 영업외수익 소계
            'non_operating_expenses': data[64],  # 영업외비용
            'interest_expenses': data[65],  # 이자비용
            'foreign_exchange_losses': data[66],  # 외환차손
            'foreign_currency_translation_losses': data[67],  # 외화환산손실
            'bad_debt_expenses_investment_assets': data[68],  # 기타 대손상각비(충당금전입액 포함)
            'donations': data[69],  # 기부금
            'loss_on_disposal_of_short_term_investments': data[70],  # 단기투자자산 처분손실
            'loss_on_disposal_of_investment_assets': data[71],  # 투자자산 처분손실
            'loss_on_disposal_of_tangible_and_intangible_assets': data[72],  # 유·무형자산 처분손실
            'inventory_write_off_losses': data[73],  # 재고자산 감모손실
            'losses_due_to_disasters': data[74],  # 재해손실
            'provision_expenses': data[75],  # 충당금·준비금 전입액
            'correction_of_prior_period_errors_loss': data[76],  # 전기오류수정손실
            'other_non_operating_expenses_subtotal': data[77],  # 기타 영업외비용 소계
            'net_income': data[78],  # 당기순손익 (영업손익 + 영업외수익 - 영업외비용)
        }

    def _get_investment_details(self, data: tuple) -> dict:
        return {
            'invest_date': data[0],  # 투자일자
            'invest_amount': self._preprocess_digit_value(data[1]),  # 투자금액
            'change_amount': self._preprocess_digit_value(data[2]),  # 변경사항(잔액)
        }

    def _get_venture_business_certificate_details(self, data: tuple) -> dict:
        return {
            'certificate_no': data[0],  # 순서번호
            'certificate_type': data[1],  # 벤처기업확인서 유형
            'announcement_date': data[2],  # 공고일자
            'validity_period': data[3],  # 유효기간
            'certificate_number': data[4].split('\n')[0].strip(),  # 확인번호 (공백 제거)
            'certificate_date': data[5],  # 확인일자
            'changes': data[6],  # 변경사항
        }

    def _search_id_from_df(self, biz_no: str) -> Optional[int]:
        """회사 정보 DataFrame에서 biz_no를 이용해 id를 찾는 함수

        Args:
            biz_no (str): 사업자등록번호

        Returns:
            Optional[int]: id
        """
        try:
            if self._comp_id_df.empty or self._comp_id_df is None:
                return None
            if self._comp_id_df[self._comp_id_df['biz_num'] == biz_no].empty:
                return None
            return self._comp_id_df[self._comp_id_df['biz_num'] == biz_no]['id'].values[0]
        except Exception as e:
            self._logger.error(f'회사 정보 DataFrame에서 biz_no를 이용해 id를 찾는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def _get_company_info(self, driver: webdriver.Chrome, vnia_sn: str) -> Optional[dict]:
        """회사 정보를 가져오는 함수

        Args:
            driver (webdriver.Chrome): ChromeDriver

        Returns:
            Optional[dict]: 회사 정보
        """
        result = deepcopy(self.company_info)
        try:
            self._logger.info(f'{vnia_sn} - 회사 정보를 가져옵니다.')
            print(f'{vnia_sn} - 회사 정보를 가져옵니다.')
            table_xpath = '//*[@id="real_contents"]/div/div[1]/div[1]/table/tbody/tr'
            temp_company_info = []
            table_tr_ls = driver.find_elements(By.XPATH, table_xpath)
            for tr in table_tr_ls:
                row = tr.find_elements(By.TAG_NAME, 'td')
                for item in row:
                    temp_company_info.append(item.text.strip())

            result['company_nm'] = temp_company_info[0]
            result['representative_nm'] = temp_company_info[1]
            result['corp_no'] = temp_company_info[2].replace('-', '')
            result['indsty_cd'] = self._vntr_dict.get(vnia_sn)
            result['indsty_nm'] = temp_company_info[3]
            result['main_prod'] = temp_company_info[4]
            result['biz_no'] = temp_company_info[5].replace('-', '')
            result['tel_no'] = temp_company_info[6]
            result['address'] = temp_company_info[7]
            result['company_id'] = self._search_id_from_df(result['biz_no'])
            return result
        except NoSuchElementException:
            self._logger.error(f'{vnia_sn} - 회사 정보가 없습니다.')
            print(f'{vnia_sn} - 회사 정보가 없습니다.')
            return None
        except Exception as e:
            self._logger.error(f'회사 정보를 가져오는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def _get_company_finance(self, driver: webdriver.Chrome, company_info: dict) -> Optional[dict]:
        """회사 재무정보를 가져오는 함수

        Args:
            driver (webdriver.Chrome): ChromeDriver
            company_info (dict): 회사 정보

        Returns:
            Optional[dict]: 회사 재무정보
        """
        result = deepcopy(self.company_finance)
        try:
            self._logger.info(f'{company_info["company_nm"]} - 회사 재무정보를 가져옵니다.')
            print(f'{company_info["company_nm"]} - 회사 재무정보를 가져옵니다.')
            # 재무정보 탭 클릭
            financial_info_tab = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/ul/li[2]/a')
            financial_info_tab.click()
            time.sleep(1)
            # 대차대조표 가져오기 (이미 기본으로 선택되어 있음) -> 리스트로 가져오기 [2019, 2018, ...]
            bs_xpath_format_l = '//*[@id="real_contents"]/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div[1]/table/tbody/tr[{}]/td' # 1 ~ 57
            bs_xpath_format_r = '//*[@id="real_contents"]/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div[2]/table/tbody/tr[{}]/td' # 1 ~ 27
            temp_bs = []
            bs_years = driver.find_elements(By.XPATH, '//*[@id="real_contents"]/div/div[1]/div[2]/div/div[1]/div[2]/div[2]/div[1]/table/thead/tr')
            bs_years = [year.text for year in bs_years][0].split(' ')[1:]
            temp_bs.append(bs_years)
            for i in range(1, 58):
                temp_bs.append(self._get_financial_info(driver, bs_xpath_format_l.format(i)))
            for i in range(1, 28):
                temp_bs.append(self._get_financial_info(driver, bs_xpath_format_r.format(i)))

            # 손익계산서 가져오기
            # 손익계산서 탭 클릭
            income_statement_tab = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/div[1]/div[2]/ul/li[2]/a')
            income_statement_tab.click()
            time.sleep(1)

            # 손익계산서 가져오기 -> 리스트로 가져오기 [2019, 2018, ...]
            is_xpath_format = '//*[@id="real_contents"]/div/div[1]/div[2]/div/div[2]/div[2]/table/tbody/tr[{}]/td' # 1 ~ 78
            temp_is = []
            is_years = driver.find_elements(By.XPATH, '//*[@id="real_contents"]/div/div[1]/div[2]/div/div[2]/div[2]/table/thead/tr')
            is_years = [year.text for year in is_years][0].split(' ')[1:]
            temp_is.append(is_years)
            for i in range(1, 79):
                temp_is.append(self._get_financial_info(driver, is_xpath_format.format(i)))

            # 연도별로 분리 -> zip으로 묶어서 리스트로 만들기
            bs_list = list(zip(*temp_bs))
            is_list = list(zip(*temp_is))

            result['company_id'] = company_info['company_id']
            result['company_nm'] = company_info['company_nm']
            result['corp_no'] = company_info['corp_no']
            result['biz_no'] = company_info['biz_no']
            for bs in bs_list:
                result['balance_sheet'].append(self._get_balance_sheet(bs))
            for is_ in is_list:
                result['income_statement'].append(self._get_income_statement(is_))
            return result
        except NoSuchElementException:
            self._logger.error(f'{company_info["company_nm"]} - 회사 재무정보가 없습니다.')
            print(f'{company_info["company_nm"]} - 회사 재무정보가 없습니다.')
            return None
        except Exception as e:
            self._logger.error(f'회사 재무정보를 가져오는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def _get_investment_info(self, driver: webdriver.Chrome, company_info: dict) -> Optional[dict]:
        """투자정보를 가져오는 함수

        Args:
            driver (webdriver.Chrome): ChromeDriver
            company_info (dict): 회사 정보

        Returns:
            Optional[dict]: 투자정보
        """
        result = deepcopy(self.investment_info)
        try:
            self._logger.info(f'{company_info["company_nm"]} - 투자정보를 가져옵니다.')
            print(f'{company_info["company_nm"]} - 투자정보를 가져옵니다.')
            # 투자정보 탭 클릭
            investment_info_tab = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/ul/li[3]/a')
            investment_info_tab.click()

            # 투자정보 가져오기
            result['company_id'] = company_info['company_id']
            result['company_nm'] = company_info['company_nm']
            result['corp_no'] = company_info['corp_no']
            result['biz_no'] = company_info['biz_no']
            # 투자정보 테이블 바디 가져오기
            ii_body_xpath = '//*[@id="real_contents"]/div/div[1]/div[3]/div[2]/table/tbody'
            ii_body = driver.find_element(By.XPATH, ii_body_xpath)

            # 투자정보 테이블 바디의 행 가져오기
            ii_rows = ii_body.find_elements(By.TAG_NAME, "tr")
            for row in ii_rows:
                # 투자정보 테이블 바디의 행의 셀 가져오기
                ii_cells = row.find_elements(By.TAG_NAME, "td")
                data = [cell.text for cell in ii_cells]
                if (len(data) < 3) or (data[0] in '투자정보 내용이 없습니다.'):
                    data = ('', '', '')
                result['investment_details'].append(self._get_investment_details(data))
            return result
        except NoSuchElementException:
            self._logger.error(f'{company_info["company_nm"]} - 투자정보가 없습니다.')
            print(f'{company_info["company_nm"]} - 투자정보가 없습니다.')
            return None
        except Exception as e:
            self._logger.error(f'투자정보를 가져오는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def _get_venture_business_certificate(self, driver: webdriver.Chrome, company_info: dict) -> Optional[dict]:
        """벤처기업확인서를 가져오는 함수

        Args:
            driver (webdriver.Chrome): ChromeDriver
            company_info (dict): 회사 정보

        Returns:
            Optional[dict]: 벤처기업확인서
        """
        result = deepcopy(self.venture_business_certificate)
        try:
            self._logger.info(f'{company_info["company_nm"]} - 벤처기업확인서를 가져옵니다.')
            print(f'{company_info["company_nm"]} - 벤처기업확인서를 가져옵니다.')
            # 벤처기업확인서 탭 클릭
            venture_certificate_tab = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/ul/li[4]/a')
            venture_certificate_tab.click()

            result['company_id'] = company_info['company_id']
            result['company_nm'] = company_info['company_nm']
            result['corp_no'] = company_info['corp_no']
            result['biz_no'] = company_info['biz_no']

            # 벤처기업확인서 테이블 바디 가져오기
            vc_body_xpath = '//*[@id="real_contents"]/div/div[1]/div[4]/div[2]/div[2]/table/tbody'
            vc_body = driver.find_element(By.XPATH, vc_body_xpath)

            # 벤처기업확인서 테이블 바디의 행 가져오기
            vc_rows = vc_body.find_elements(By.TAG_NAME, "tr")
            for row in vc_rows:
                # 벤처기업확인서 테이블 바디의 행의 셀 가져오기
                vc_cells = row.find_elements(By.TAG_NAME, "td")
                data = [cell.text for cell in vc_cells]
                if len(data) < 7:
                    data = ('', '', '', '', '', '', '')
                result['certificate_details'].append(self._get_venture_business_certificate_details(data))
            return result
        except NoSuchElementException:
            self._logger.error(f'{company_info["company_nm"]} - 벤처기업확인서가 없습니다.')
            print(f'{company_info["company_nm"]} - 벤처기업확인서가 없습니다.')
            return None
        except Exception as e:
            self._logger.error(f'벤처기업확인서를 가져오는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def _get_vntr_details(self, driver: webdriver.Chrome, vnia_sn: str, captcha_key: str) -> Optional[dict]:
        """벤처기업 상세정보를 가져오는 함수

        Args:
            vnia_sn (str): 벤처기업일련번호
            captcha_key (str): 캡챠 키

        Returns:
            Optional[dict]: 벤처기업 상세정보
        """
        try:
            self._init_data()
            self._logger.info(f'{vnia_sn} - 벤처기업 상세정보를 가져옵니다.')
            print(f'{vnia_sn} - 벤처기업 상세정보를 가져옵니다.')
            # 벤처기업 상세정보 URL
            detail_url = f'https://www.smes.go.kr/venturein/pbntc/searchVntrCmpDtls?vniaSn={vnia_sn}&captcha={captcha_key}'
            # 벤처기업 상세정보 페이지로 이동
            driver.get(detail_url)
            # 연결된 페이지에 //*[@id="real_contents"]/h2 의 텍스트가 '벤처기업 상세정보' 인지 확인
            title = driver.find_element(By.XPATH, '//*[@id="real_contents"]/h2')
            if title.text != '벤처기업 상세정보':
                return None

            # 회사 정보 가져오기
            company_info = self._get_company_info(driver, vnia_sn)
            if company_info is None:
                return None
            # 회사 재무정보 가져오기
            company_finance = self._get_company_finance(driver, company_info)
            if company_finance is None:
                return None
            # 투자정보 가져오기
            investment_info = self._get_investment_info(driver, company_info)
            if investment_info is None:
                return None
            # 벤처기업확인서 가져오기
            venture_business_certificate = self._get_venture_business_certificate(driver, company_info)
            if venture_business_certificate is None:
                return None

            result = {
                'company_info': company_info,
                'company_finance': company_finance,
                'investment_info': investment_info,
                'venture_business_certificate': venture_business_certificate,
            }
            return result
        except Exception as e:
            self._logger.error(f'벤처기업 상세정보를 가져오는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def _check_company_info_with_pydantic(
        self, company_info: dict
    ) -> Optional[CollectVntrInfoPydantic]:
        try:
            # pydantic 모델로 변환
            company_info = CollectVntrInfoPydantic(**company_info)
            return company_info
        except Exception as e:
            self._logger.error(f'회사 정보를 pydantic 모델로 변환하는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def _check_company_finance_with_pydantic(
        self, company_finance: dict
    ) -> Optional[Tuple[List[CollectVntrFinanceBalancePydantic], List[CollectVntrFinanceIncomePydantic]]]:
        try:
            base_company_finance = {
                'company_id': company_finance['company_id'],
                'company_nm': company_finance['company_nm'],
                'corp_no': company_finance['corp_no'],
                'biz_no': company_finance['biz_no'],
            }
            all_company_bs = []
            for bs in company_finance['balance_sheet']:
                if list(bs.values()) != [''] * len(bs):
                    company_bs_temp = base_company_finance.copy()
                    company_bs_temp.update(bs)
                    all_company_bs.append(company_bs_temp.copy())
            all_company_is = []
            for inc in company_finance['income_statement']:
                if list(inc.values()) != [''] * len(inc):
                    company_is_temp = base_company_finance.copy()
                    company_is_temp.update(inc)
                    all_company_is.append(company_is_temp)

            if all_company_bs:
                all_company_bs = [CollectVntrFinanceBalancePydantic(**company_bs) for company_bs in all_company_bs]
            if all_company_is:
                all_company_is = [CollectVntrFinanceIncomePydantic(**company_is) for company_is in all_company_is]
            return all_company_bs, all_company_is
        except Exception as e:
            self._logger.error(f'회사 재무정보를 pydantic 모델로 변환하는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None, None

    def _check_investment_info_with_pydantic(
        self, investment_info: dict
    ) -> Optional[List[CollectVntrInvestmentInfoPydantic]]:
        try:
            base_investment_info = {
                'company_id': investment_info['company_id'],
                'company_nm': investment_info['company_nm'],
                'corp_no': investment_info['corp_no'],
                'biz_no': investment_info['biz_no'],
            }
            all_investment_info = []
            for ii in investment_info['investment_details']:
                if list(ii.values()) != [''] * len(ii):
                    investment_info_temp = base_investment_info.copy()
                    investment_info_temp.update(ii)
                    all_investment_info.append(investment_info_temp)
            if all_investment_info:
                all_investment_info = [CollectVntrInvestmentInfoPydantic(**investment_info) for investment_info in all_investment_info]
            return all_investment_info
        except Exception as e:
            self._logger.error(f'투자정보를 pydantic 모델로 변환하는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def _check_venture_business_certificate_with_pydantic(
        self, venture_business_certificate: dict
    ) -> Optional[List[CollectVntrCertificatePydantic]]:
        try:
            base_venture_business_certificate = {
                'company_id': venture_business_certificate['company_id'],
                'company_nm': venture_business_certificate['company_nm'],
                'corp_no': venture_business_certificate['corp_no'],
                'biz_no': venture_business_certificate['biz_no'],
            }
            all_venture_business_certificate = []
            for vc in venture_business_certificate['certificate_details']:
                if list(vc.values()) != [''] * len(vc):
                    venture_business_certificate_temp = base_venture_business_certificate.copy()
                    venture_business_certificate_temp.update(vc)
                    all_venture_business_certificate.append(venture_business_certificate_temp)

            if all_venture_business_certificate:
                all_venture_business_certificate = [CollectVntrCertificatePydantic(**venture_business_certificate) for venture_business_certificate in all_venture_business_certificate]
            return all_venture_business_certificate
        except Exception as e:
            self._logger.error(f'벤처기업확인서를 pydantic 모델로 변환하는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def scrape_vntr(self, vntr_list: list, scraper_name: str):
        vntr_queue = deque(vntr_list)
        total_vntr_count = len(vntr_queue)
        while vntr_queue:
            print(f'[{scraper_name}] 남은 벤처기업 수: {len(vntr_queue)} / {total_vntr_count} (진행 상황: {round((total_vntr_count - len(vntr_queue)) / total_vntr_count * 100, 2)}%)')
            is_success = False
            vnia_sn = vntr_queue.popleft()
            try:
                # 캡챠 키가 맞을 때까지 반복 -> 5번 반복
                try_count = 5
                while try_count > 0:
                    driver = self._get_driver(self.captcha_url)
                    try_count -= 1
                    captcha_key = self._get_captcha_key(driver)
                    if captcha_key is None:
                        driver.quit()
                        time.sleep(2)
                        continue
                    # 캡챠키가 숫자 6자리인지 확인
                    if not captcha_key.isdigit() or len(captcha_key) != 6:
                        driver.quit()
                        time.sleep(2)
                        continue
                    vntr_details = self._get_vntr_details(driver, vnia_sn, captcha_key)
                    if vntr_details is None:
                        driver.quit()
                        time.sleep(2)
                        continue
                    break
                if vntr_details:
                    company_info = vntr_details['company_info']
                    company_finance = vntr_details['company_finance']
                    investment_info = vntr_details['investment_info']
                    venture_business_certificate = vntr_details['venture_business_certificate']
                    # pydantic 모델로 변환
                    company_info = self._check_company_info_with_pydantic(company_info)
                    all_company_bs, all_company_is = self._check_company_finance_with_pydantic(company_finance)
                    all_investment_info = self._check_investment_info_with_pydantic(investment_info)
                    all_venture_business_certificate = self._check_venture_business_certificate_with_pydantic(venture_business_certificate)

                    # DB에 저장
                    msg, is_success = collections_db.insert_all_vntr_data(
                        vntr_info=company_info,
                        vntr_finance_balance=all_company_bs,
                        vntr_finance_income=all_company_is,
                        vntr_investment=all_investment_info,
                        vntr_certificate=all_venture_business_certificate
                    )
                    self._logger.info(msg)
                    print(f'--- {msg} ---\n')
            except Exception as e:
                self._logger.error(f'[{scraper_name}]벤처기업 상세정보를 가져오는데 실패했습니다. {e}')
                self._logger.error(traceback.format_exc())
                print(f'[{scraper_name}]벤처기업 상세정보를 가져오는데 실패했습니다. {e}')
                driver.quit()
                continue
            finally:
                driver.quit()
                if not is_success:
                    vntr_queue.append(vnia_sn)
                    time.sleep(2)
                    continue
        self._logger.info(f'[{scraper_name}]벤처기업 상세정보를 모두 가져왔습니다.')
        print(f'[{scraper_name}]벤처기업 상세정보를 모두 가져왔습니다.')

    def scrape(self):
        try:
            vntr_list = self._get_vntr_list()
            # 8개로 나누어서 크롤링
            vntr_list_1 = vntr_list[:len(vntr_list) // 8]
            vntr_list_2 = vntr_list[len(vntr_list) // 8: len(vntr_list) // 8 * 2]
            vntr_list_3 = vntr_list[len(vntr_list) // 8 * 2: len(vntr_list) // 8 * 3]
            vntr_list_4 = vntr_list[len(vntr_list) // 8 * 3: len(vntr_list) // 8 * 4]
            vntr_list_5 = vntr_list[len(vntr_list) // 8 * 4: len(vntr_list) // 8 * 5]
            vntr_list_6 = vntr_list[len(vntr_list) // 8 * 5: len(vntr_list) // 8 * 6]
            vntr_list_7 = vntr_list[len(vntr_list) // 8 * 6: len(vntr_list) // 8 * 7]
            vntr_list_8 = vntr_list[len(vntr_list) // 8 * 7:]

            #  threadpoolexecutor 사용
            executors_list = []
            with ThreadPoolExecutor(max_workers=8) as executor:
                executors_list.append(executor.submit(self.scrape_vntr, vntr_list_1, 'SCP 1'))
                executors_list.append(executor.submit(self.scrape_vntr, vntr_list_2, 'SCP 2'))
                executors_list.append(executor.submit(self.scrape_vntr, vntr_list_3, 'SCP 3'))
                executors_list.append(executor.submit(self.scrape_vntr, vntr_list_4, 'SCP 4'))
                executors_list.append(executor.submit(self.scrape_vntr, vntr_list_5, 'SCP 5'))
                executors_list.append(executor.submit(self.scrape_vntr, vntr_list_6, 'SCP 6'))
                executors_list.append(executor.submit(self.scrape_vntr, vntr_list_7, 'SCP 7'))
                executors_list.append(executor.submit(self.scrape_vntr, vntr_list_8, 'SCP 8'))

            for executor in executors_list:
                pass
            self._logger.info('벤처기업 상세정보를 모두 가져왔습니다.')
            print('벤처기업 상세정보를 모두 가져왔습니다.')
        except Exception as e:
            self._logger.error(f'벤처기업 상세정보를 가져오는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            print(f'벤처기업 상세정보를 가져오는데 실패했습니다. {e}\n 자세한 내용은 {self._log_file} 파일을 확인해주세요.')
