import time
import traceback
import json
from typing import Optional
from collections import deque

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from app.config.settings import FILE_PATHS, TROCR_API_TOKEN
from app.common.core.utils import make_dir, get_current_datetime
from app.common.log.log_config import setup_logger
from app.scrapers.vnia_list_scraper import VniaListScraper

class VniaScraper:
    def __init__(self) -> None:
        self._data_path = FILE_PATHS['data']
        self._log_path = FILE_PATHS['log'] + 'vnia_scraper'
        self._driver_path = FILE_PATHS['chromedriver']

        make_dir(self._log_path)
        self._log_file = self._log_path + f'/{get_current_datetime()}.log'
        self._logger = setup_logger(
            'vnia_scraper',
            self._log_file
        )

        self.captcha_url = "https://www.smes.go.kr/venturein/pbntc/captchaImg.do"
        self._api_url = "https://api-inference.huggingface.co/models/microsoft/trocr-base-printed"
        self._api_headers = {"Authorization": f"Bearer {TROCR_API_TOKEN}"}

    def _init_data(self) -> None:
        """데이터를 초기화하는 함수
        """
        self.company_info = {
            'company_nm': None,
            'representative_nm': None,
            'corp_no': None,
            'biz_nm': None,
            'main_prod': None,
            'biz_no': None,
            'tel_no': None,
            'address': None,
        }
        self.company_finance = {
            'company_nm': None,
            'corp_no': None,
            'biz_no': None,
            'balance_sheet': [],
            'income_statement': [],
        }
        self.investment_info = {
            'company_nm': None,  # 회사명
            'corp_no': None,
            'biz_no': None,
            'investment_details': [],  # 투자정보 상세정보
        }
        self.venture_business_certificate = {
            'company_nm': None,  # 회사명
            'corp_no': None,
            'biz_no': None,
            'certificate_details': [],  # 벤처기업확인서 상세정보
        }

    def _get_vnia_list(self) -> Optional[list]:
        """벤처기업 인증번호 목록을 가져오는 함수
        
        Returns:
            Optional[list]: 벤처기업 인증번호 목록
        """
        try:
            vnia_list_scraper = VniaListScraper()
            vnia_list = vnia_list_scraper.read_vnia_sn_list()
            return vnia_list
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
            self._logger.info(f'ChromeDriver를 가져옵니다.')
            print(f'ChromeDriver를 가져옵니다.')
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-dev-shm-usage")
            # chrome_options.add_argument("--disable-gpu")

            driver = webdriver.Chrome(
                service=ChromeService(
                    executable_path=self._driver_path
                    ),
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
            'type': data[1],  # 벤처기업확인서 유형
            'announcement_date': data[2],  # 공고일자
            'validity_period': data[3],  # 유효기간
            'certificate_number': data[4].split('\n')[0].strip(),  # 확인번호 (공백 제거)
            'certificate_date': data[5],  # 확인일자
            'changes': data[6],  # 변경사항
        }

    def _get_company_info(self, driver: webdriver.Chrome) -> Optional[dict]:
        """회사 정보를 가져오는 함수

        Args:
            driver (webdriver.Chrome): ChromeDriver

        Returns:
            Optional[dict]: 회사 정보
        """
        result = self.company_info.copy()
        try:
            self._logger.info(f'회사 정보를 가져옵니다.')
            print(f'회사 정보를 가져옵니다.')
            company_nm = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/div[1]/div[1]/table/tbody/tr[1]/td')
            representative_nm = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/div[1]/div[1]/table/tbody/tr[2]/td[1]')
            corp_no = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/div[1]/div[1]/table/tbody/tr[2]/td[2]')
            biz_nm = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/div[1]/div[1]/table/tbody/tr[3]/td[1]')
            main_prod = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/div[1]/div[1]/table/tbody/tr[3]/td[2]')
            biz_no = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/div[1]/div[1]/table/tbody/tr[4]/td[1]')
            tel_no = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/div[1]/div[1]/table/tbody/tr[4]/td[2]')
            address = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/div[1]/div[1]/table/tbody/tr[5]/td')

            result['company_nm'] = company_nm.text
            result['representative_nm'] = representative_nm.text
            result['corp_no'] = corp_no.text
            result['biz_nm'] = biz_nm.text
            result['main_prod'] = main_prod.text
            result['biz_no'] = biz_no.text.replace('-', '')
            result['tel_no'] = tel_no.text
            result['address'] = address.text
            
            # json으로 보기
            print(json.dumps(result, indent=4, ensure_ascii=False))
            return result
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
        result = self.company_finance.copy()
        try:
            self._logger.info(f'회사 재무정보를 가져옵니다.')
            print(f'회사 재무정보를 가져옵니다.')
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

            result['company_nm'] = company_info['company_nm']
            result['corp_no'] = company_info['corp_no']
            result['biz_no'] = company_info['biz_no']
            for bs in bs_list:
                result['balance_sheet'].append(self._get_balance_sheet(bs))
            for is_ in is_list:
                result['income_statement'].append(self._get_income_statement(is_))

            # json 형태로 보기
            print(json.dumps(result, indent=4, ensure_ascii=False))
            return result
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
        result = self.investment_info.copy()
        try:
            self._logger.info(f'투자정보를 가져옵니다.')
            print(f'투자정보를 가져옵니다.')
            # 투자정보 탭 클릭
            investment_info_tab = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/ul/li[3]/a')
            investment_info_tab.click()

            # 투자정보 가져오기
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
                result['investment_details'].append(self._get_investment_details(data))

            # json 형태로 보기
            print(json.dumps(result, indent=4, ensure_ascii=False))
            return result
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
        result = self.venture_business_certificate.copy()
        try:
            self._logger.info(f'벤처기업확인서를 가져옵니다.')
            print(f'벤처기업확인서를 가져옵니다.')
            # 벤처기업확인서 탭 클릭
            venture_certificate_tab = driver.find_element(By.XPATH, '//*[@id="real_contents"]/div/ul/li[4]/a')
            venture_certificate_tab.click()

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
                result['certificate_details'].append(self._get_venture_business_certificate_details(data))

            # json 형태로 보기
            print(json.dumps(result, indent=4, ensure_ascii=False))
            return result
        except Exception as e:
            self._logger.error(f'벤처기업확인서를 가져오는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def _get_vnia_details(self, driver: webdriver.Chrome, vnia_sn: str, captcha_key: str) -> Optional[dict]:
        """벤처기업 상세정보를 가져오는 함수

        Args:
            vnia_sn (str): 벤처기업일련번호
            captcha_key (str): 캡챠 키

        Returns:
            Optional[dict]: 벤처기업 상세정보
        """
        try:
            self._logger.info(f'벤처기업 상세정보를 가져옵니다.')
            print(f'벤처기업 상세정보를 가져옵니다.')
            # 벤처기업 상세정보 URL
            detail_url = f'https://www.smes.go.kr/venturein/pbntc/searchVntrCmpDtls?vniaSn={vnia_sn}&captcha={captcha_key}'
            # 벤처기업 상세정보 페이지로 이동
            driver.get(detail_url)
            # 연결된 페이지에 //*[@id="real_contents"]/h2 의 텍스트가 '벤처기업 상세정보' 인지 확인
            title = driver.find_element(By.XPATH, '//*[@id="real_contents"]/h2')
            if title.text != '벤처기업 상세정보':
                return None

            # 회사 정보 가져오기
            company_info = self._get_company_info(driver)
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

            # json 형태로 보기
            print(json.dumps(result, indent=4, ensure_ascii=False))
            return result
        except Exception as e:
            self._logger.error(f'벤처기업 상세정보를 가져오는데 실패했습니다. {e}')
            self._logger.error(traceback.format_exc())
            return None

    def scrape_vnia(self):
        vnia_queue = deque(self._get_vnia_list())
        while vnia_queue:
            print(f'남은 벤처기업 수: {len(vnia_queue)}')
            is_success = False
            vnia_sn = vnia_queue.popleft()
            driver = self._get_driver()
            try:
                # 캡챠 키가 맞을 때까지 반복 -> 5번 반복
                try_count = 5
                while try_count > 0:
                    try_count -= 1
                    captcha_key = self._get_captcha_key(driver)
                    if captcha_key is None:
                        continue
                    vnia_details = self._get_vnia_details(driver, vnia_sn, captcha_key)
                    if vnia_details is None:
                        continue
                    break
                if vnia_details:
                    company_info = vnia_details['company_info']
                    company_finance = vnia_details['company_finance']
                    investment_info = vnia_details['investment_info']
                    venture_business_certificate = vnia_details['venture_business_certificate']
                    self._save_company_info(company_info)
                    self._save_company_finance(company_finance)
                    self._save_investment_info(investment_info)
                    self._save_venture_business_certificate(venture_business_certificate)
                    is_success = True
            except Exception as e:
                self._logger.error(f'벤처기업 상세정보를 가져오는데 실패했습니다. {e}')
                self._logger.error(traceback.format_exc())
                continue
            finally:
                driver.quit()
                if not is_success:
                    vnia_queue.append(vnia_sn)
                    time.sleep(5)
                    continue
        self._logger.info(f'벤처기업 상세정보를 모두 가져왔습니다.')
        print(f'벤처기업 상세정보를 모두 가져왔습니다.')
