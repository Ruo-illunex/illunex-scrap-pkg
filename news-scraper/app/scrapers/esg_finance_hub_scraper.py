import re
import csv
import datetime
import traceback

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from app.scrapers.urls import URLs
from app.config.settings import FILE_PATHS
from app.common.log.log_config import setup_logger


class EsgFinanceHubScraper:

    def __init__(self, scraper_name: str, headless: bool = True) -> None:
        self.scraper_name = scraper_name
        self.current_datetime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.logger = setup_logger(
            __name__,
            f'app/log/{self.scraper_name}/{self.scraper_name}_{self.current_datetime}.log',
            )
        self.logger.info("ESG_FINANCE_HUB_SCRAPER INITIALIZED")

        self.chrome_options = Options()
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        if headless:
            self.chrome_options.add_argument("--headless")
        else:
            self.chrome_options.add_argument("--disable-gpu")

        self.current_date = datetime.datetime.now().strftime("%Y%m%d")
        self.filename = f"app/data/{self.scraper_name}_links_{self.current_date}.csv"
        self.news_board_url = URLs(self.scraper_name).urls['news_board_url']
        self.driver_path = FILE_PATHS['chromedriver']
        self.driver = None
        self.get_driver()

        self.last_page = 172
        self.current_page = 1
        self.go_to_last_page_and_find_last_page_number()    # 게시판의 마지막 페이지로 이동하여 실제 마지막 페이지 번호를 찾음
        self.find_last_saved_page()                        # CSV 파일에서 마지막으로 저장된 페이지 번호를 찾음 (없으면 1)

        self.all_links = {}    # {페이지 번호: [링크1, 링크2, ...]} 형태의 딕셔너리


    # 드라이버를 초기화하는 함수
    def get_driver(self):
        try:
            self.driver = webdriver.Chrome(service=ChromeService(executable_path=self.driver_path), options=self.chrome_options)
            self.driver.get(self.news_board_url)

            info_message = f"DRIVER WAS INITIALIZED WITH {self.news_board_url}"
            self.logger.info(info_message)
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE GETTING DRIVER.\n{stack_trace}\n{e}"
            self.logger.error(err_message)


    # 로딩 모달이 사라질 때까지 대기하는 함수
    def wait_for_loading_to_disappear(self):
        try:
            # 로딩 모달이 사라질 때까지 최대 30초간 대기
            WebDriverWait(self.driver, 30).until(
                EC.invisibility_of_element((By.CLASS_NAME, "loading-modal"))
            )
        except TimeoutException:
            err_message = "TIMEOUT EXCEPTION: LOADING MODAL DID NOT DISAPPEAR"
            self.logger.error(err_message)


    # CSV 파일을 저장하는 함수
    def save_links_to_csv(self):
        try:
            with open(self.filename, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                for link in self.all_links[self.current_page]:
                    writer.writerow([self.current_page, link])
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE SAVING LINKS TO {self.filename}"
            self.logger.error(err_message)
            self.logger.error(stack_trace)
            self.logger.error(e)


    # 마지막으로 저장된 페이지 번호를 찾는 함수
    def find_last_saved_page(self):
        try:
            with open(self.filename, 'r', newline='', encoding='utf-8') as file:
                for row in csv.reader(file):
                    if row:  # 빈 줄이 아닌 경우에만 처리
                        self.current_page = int(row[0]) + 1
                info_message = f"LAST PAGE NUMBER: {self.current_page - 1}\nCONTINUE FROM THE NEXT PAGE"
                self.logger.info(info_message)
        except FileNotFoundError:
            info_message = f"FILE NOT FOUND: {self.filename}. STARTING FROM THE FIRST PAGE."
            self.logger.info(info_message)


    # 마지막 페이지로 이동하여 실제 마지막 페이지 번호를 찾는 함수
    def go_to_last_page_and_find_last_page_number(self):
        try:
            # '마지막으로' 버튼을 클릭하여 마지막 페이지로 이동
            last_page_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.last"))
            )
            last_page_button.click()

            # 로딩 모달이 사라질 때까지 기다림
            self.wait_for_loading_to_disappear()

            # 페이지 로드 후, 페이지네이션에서 실제 마지막 페이지 번호를 찾음
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.paging > li > a"))
            )
            page_numbers = self.driver.find_elements_by_css_selector("ul.paging > li > a")
            # 페이지 번호가 숫자인 요소만 필터링
            numeric_page_numbers = [elem.text for elem in page_numbers if elem.text.isdigit()]
            
            # 마지막 페이지 번호 추출
            if numeric_page_numbers:
                self.last_page = max(map(int, numeric_page_numbers))
                info_message = f"LAST PAGE NUMBER: {self.last_page}"
                self.logger.info(info_message)
            # 페이지 번호가 없는 경우
            else:
                err_message = "NO PAGE NUMBERS WERE FOUND AND RETURNED 172"
                self.logger.error(err_message)
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = "THERE WAS AN ERROR WHILE FINDING LAST PAGE NUMBER AND RETURNED 172"
            self.logger.error(err_message)
            self.logger.error(stack_trace)
            self.logger.error(e)


    # 요소에서 URL을 추출하는 함수
    def get_link(self, element):
        # 요소의 onclick 속성에서 URL 추출
        onclick_script = element.get_attribute('onclick')
        if onclick_script:
            # 정규 표현식을 사용하여 URL 추출
            url_match = re.search(r"window.open\('([^']*)'", onclick_script)
            if url_match:
                link = url_match.group(1)
                info_message = f"URL WAS FOUND FROM {onclick_script}"
                self.logger.info(info_message)
                return link
            else:
                info_message = f"NO URL WAS FOUND FROM {onclick_script}"
                self.logger.info(info_message)
                return None
        else:
            info_message = f"NO ONCLICK SCRIPT WAS FOUND FROM {element.text}"
            self.logger.info(info_message)
            return None


    # 다음 페이지로 이동하는 함수
    def go_to_next_page(self):
        if self.current_page <= self.last_page:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[onclick*='clickPaging']"))).click()


    # 모든 페이지의 링크를 추출하여 CSV 파일에 저장하는 함수
    def get_all_links_and_save_to_csv(self):
        if self.driver is None:
            err_message = "DRIVER IS NONE. EXITING."
            self.logger.error(err_message)
            return None
        try:
            self.logger.info("STARTING ESG_FINANCE_HUB_SCRAPER")

            # 로딩 모달이 사라질 때까지 대기
            self.wait_for_loading_to_disappear()

            # 30개씩 보기 설정
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "search_cnt_combo"))).click()
            self.driver.find_element(By.CSS_SELECTOR, "option[value='30']").click()            

            # 모든 페이지에 대해 반복
            while self.current_page <= self.last_page:
                try:
                    info_message = f"CURRENT PAGE: {self.current_page}"
                    self.logger.info(info_message)

                    # 로딩 모달이 사라질 때까지 대기
                    self.wait_for_loading_to_disappear()

                    WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.word-item")))
                    word_items = self.driver.find_elements(By.CSS_SELECTOR, "span.word-item")
                    # 유효하지 않은 링크는 건너뛰고, 유효한 링크만 딕셔너리에 현재 페이지의 링크들을 저장
                    self.all_links[self.current_page] = [self.get_link(item) for item in word_items if self.get_link(item)]

                    # 현재 페이지의 링크들을 CSV 파일에 저장
                    self.save_links_to_csv()

                    # 다음 페이지로 이동
                    self.current_page += 1
                    self.go_to_next_page()

                except TimeoutException:
                    err_message = "TIMEOUT EXCEPTION: PAGE DID NOT LOAD"
                    self.logger.error(err_message)
                    # 다음 페이지로 이동
                    self.current_page += 1
                    self.go_to_next_page()
                
                except NoSuchElementException:
                    err_message = "NO SUCH ELEMENT EXCEPTION: PAGE DID NOT LOAD"
                    self.logger.error(err_message)
                    # 다음 페이지로 이동
                    self.current_page += 1
                    self.go_to_next_page()

        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE GETTING ALL LINKS AND SAVING TO CSV.\n{stack_trace}\n{e}"
            self.logger.error(err_message)
            return None

        finally:
            info_message = "CLOSING DRIVER"
            self.logger.info(info_message)
            self.driver.quit()


# ESG 파이낸스 허브 스크레이퍼 실행함수
def scrape_esg_finance_hub():
    scraper_name = "esg_finance_hub"
    esg_finance_hub_scraper = EsgFinanceHubScraper(scraper_name=scraper_name)
    esg_finance_hub_scraper.get_all_links_and_save_to_csv()


if __name__ == "__main__":
    scrape_esg_finance_hub()
