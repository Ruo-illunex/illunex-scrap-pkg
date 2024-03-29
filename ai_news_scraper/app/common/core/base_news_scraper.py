import abc
import datetime
from typing import Generator, Optional
import traceback
import json
import asyncio
from collections import deque
import hashlib

import aiohttp
import requests
from bs4 import BeautifulSoup
from trafilatura import fetch_url, bare_extraction

from app.common.log.log_config import setup_logger
from app.common.db.news_database import NewsDatabase
from app.common.db.scraper_manager_database import ScraperManagerDatabase
from app.models_init import ScrapSessionLog, ScrapErrorLog, ScrapManager
from app.config import settings
from app.common.messages import Messages
from app.common.core.utils import load_yaml, remove_emojis_and_special_chars


class NewsScraper(abc.ABC):
    """
    뉴스 스크래핑을 위한 추상 클래스.
    다양한 뉴스 사이트에 대한 스크래핑 클래스가 이 클래스를 상속받아 구현됩니다.
    """

    def __init__(self, scraper_name: str):
        """
        Args:
            scraper_name (str): 스크래퍼 이름
        """
        self.scraper_name = scraper_name
        self.media_name = ''
        self.current_time = self.get_current_time()
        self.logger = setup_logger(
            scraper_name,
            f'app/log/{self.scraper_name}/{self.scraper_name}_{self.current_time}.log',
            level='INFO'
            )

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            }
        self.news_db = NewsDatabase()
        self.scraper_manager_db = ScraperManagerDatabase()
        self.session = self.scraper_manager_db.SessionLocal()
        self.news_data_list = []    # 뉴스 데이터 리스트

        self.interval_time_sleep = 600   # 10분(600초)
        self.retry_delay = 5    # 5초

        self.scraped_md5s = deque(maxlen=10000)  # 최근 스크래핑한 URL MD5 저장

        self.is_duplicated = False  # 중복 여부
        # 세션 로그
        self.session_log = {
            "remarks": self.scraper_name,
        }
        self.initialize_session_log()

        # 에러 로그
        self.error_logs = []
        self.is_error = False
        self.error_log = {
            "error_message": "",
            "error_time": None,
            "url": None,
        }
        self.initialize_error_log("")
        self.parsing_rules_dict = self.get_parsing_rules_dict(self.scraper_name)
        category_data = load_yaml(settings.FILE_PATHS.get('category'))
        self.category_dict = category_data.get('category_dict')
        self.categories = category_data.get('categories').get(self.scraper_name)
        if not isinstance(self.category_dict, dict):
            err_message = f"CATEGORY YAML FILE IS NOT A DICTIONARY.\n{self.category_dict}"
            self.process_err_log_msg(err_message, "load_yaml")
            self.category_dict = {}

    # URL의 MD5 해시를 생성하는 함수
    def generate_md5(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    # 스크래핑 전 URL MD5 확인
    def is_already_scraped(self, url: str) -> bool:
        url_md5 = self.generate_md5(url)
        return url_md5 in self.scraped_md5s

    # 스크래핑 후 URL MD5 저장
    def mark_as_scraped(self, url: str):
        url_md5 = self.generate_md5(url)
        self.scraped_md5s.append(url_md5)

    # 인포, 성공, 경고 메세지 > 로그 메세지 로직
    def process_info_log_msg(self, message: str, type: str="info") -> None:
        """인포, 성공, 경고 메세지 > 로그 메세지 로직
        Args:
            message (str): 메세지
            type (str, optional): 로그 타입. Defaults to "info". (info, success, warning)
        """
        if type == "info":
            log_message = Messages.info_message(message)
            self.logger.info(log_message)
        elif type == "success":
            log_message = Messages.success_message(message)
            self.logger.info(log_message)
        elif type == "warning":
            log_message = Messages.warning_message(message)
            self.logger.warning(log_message)

    # 에러 메세지 > 로그 메세지 로직
    def process_err_log_msg(self, err_message: str, function_name: str, stack_trace: str = None, exception: Exception = None) -> None:
        """에러 메세지 > 로그 메세지 로직
        Args:
            err_message (str): 에러 메세지
            function_name (str): 함수 이름
            stack_trace (str, optional): 스택 트레이스. Defaults to None.
            exception (Exception, optional): 예외. Defaults to None.
        """
        log_message = Messages.error_message(err_message, function_name, stack_trace, exception)
        self.logger.error(log_message)
        self.is_error = True
        self.error_log['error_message'] += log_message

    # 파싱 규칙 딕셔너리 가져오기
    def get_parsing_rules_dict(self, scraper_name: str = None) -> dict:
        parsing_rules_dict = {}
        try:
            parsing_rules = self.session.query(ScrapManager).filter(ScrapManager.portal == scraper_name).all()
            if not parsing_rules:
                err_message = f"PARSING RULES IS EMPTY FOR {scraper_name}"
                self.process_err_log_msg(err_message, "get_parsing_rules_dict")
                return None

            for parsing_rule in parsing_rules:
                parsing_rule_dict = json.loads(parsing_rule.parsing_rule) if isinstance(parsing_rule.parsing_rule, str) else parsing_rule.parsing_rule

                parsing_rules_dict[parsing_rule.parsing_target_name] = (
                    parsing_rule.parsing_method,
                    parsing_rule_dict,
                )
            info_message = f"PARSING RULES SUCCESSFULLY LOADED FOR {scraper_name}"
            self.process_info_log_msg(info_message, "success")
            print(info_message)
            return parsing_rules_dict

        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE TRANSFORMING PARSING RULES TO DICTIONARY FOR {scraper_name}"
            self.process_err_log_msg(err_message, "get_parsing_rules_dict", stack_trace, e)
            return None

    # 세션 로그 초기화
    def initialize_session_log(self) -> None:
        """세션 로그 초기화"""
        self.session_log['start_time'] = self.get_current_time()
        self.session_log['end_time'] = None
        self.session_log['total_records_processed'] = 0
        self.session_log['success_count'] = 0
        self.session_log['fail_count'] = 0
        self.session_log['dup_count'] = 0
        self.is_error = False  # 에러 여부 초기화

        info_message = "SESSION LOG INITIALIZED"
        self.process_info_log_msg(info_message)

    # 에러 로그 개별 초기화
    def initialize_error_log(self, news_url: str) -> None:
        """에러 로그 개별 초기화
        Args:
            news_url (str): 뉴스 기사 URL
        Returns:
            error_log (dict): 에러 로그
        """
        # 에러 로그 개별 초기화 로직
        self.error_log['session_log_id'] = None
        self.error_log['error_message'] = ""
        self.error_log['error_time'] = None
        self.error_log['url'] = news_url
        self.is_error = False  # 에러 여부 초기화
        self.is_duplicated = False  # 중복 여부 초기화

        info_message = f"ERROR LOG INITIALIZED FOR URL: {news_url}"
        self.process_info_log_msg(info_message)

    # 현재 시간을 가져오는 함수
    def get_current_time(self) -> str:
        """현재 시간을 가져오는 함수
        Returns:
            current_time (str): 현재 시간
        """
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # soup에서 데이터 추출
    def safe_extract(self, soup, selector=None, attribute_name=None, default=None, find=False, tag=None, find_attributes=None, find_all=False):
        """
        soup에서 데이터를 안전하게 추출하는 함수.
        Args:
            soup (BeautifulSoup): BeautifulSoup 객체.
            selector (str): CSS 선택자.
            attribute_name (str): 추출할 요소의 속성 이름.
            default (str): 기본 반환값.
            find (bool): find() 함수 사용 여부.
            tag (str): 검색할 HTML 태그 이름.
            find_attributes (dict): find() 또는 find_all()에서 사용할 속성 딕셔너리.
            find_all (bool): find_all() 함수 사용 여부.

        Returns:
            str 또는 list: 추출된 데이터.
        """
        try:
            if selector:
                element = soup.select_one(selector) if not find_all else soup.select(selector)
            elif find and tag:
                element = soup.find(tag, find_attributes) if not find_all else soup.find_all(tag, find_attributes)
            else:
                return default

            if element:
                if find_all:
                    return [el.get(attribute_name, default) if attribute_name else el.get_text().strip() for el in element]
                else:
                    if attribute_name:
                        return element.get(attribute_name, default)
                    else:
                        return element.get_text().strip()
            else:
                return default

        except Exception as e:
            # 예외 발생 시 스택 트레이스 출력
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE EXTRACTING DATA."
            self.process_err_log_msg(err_message, "safe_extract", stack_trace, e)

            warning_message = f"EXTRACTED DATA IS EMPTY. RETURNING DEFAULT VALUE: {default}. CHECK IF THE PARSING RULES ARE CORRECT."
            self.process_info_log_msg(warning_message, "warning")
            return default

    def extract_element(self, soup, parsing_rule):
        """뉴스 요소를 추출하는 함수
        Args:
            soup (BeautifulSoup): BeautifulSoup 객체
            parsing_rule (dict): 파싱 규칙 딕셔너리
        Returns:
            data (str): 뉴스 요소
        """
        return self.safe_extract(
            soup,
            selector=parsing_rule['selector'],
            find=parsing_rule['find'],
            tag=parsing_rule['tag'],
            find_attributes=parsing_rule['find_attributes'],
            attribute_name=parsing_rule['attribute_name'],
            default=parsing_rule['default'],
            find_all=parsing_rule['find_all']
        )

    def extract_news_details(self, soup, elements: list, parsing_rules_dict: dict = None) -> dict:
        """뉴스 상세 정보를 추출하는 함수
        Args:
            soup (BeautifulSoup): BeautifulSoup 객체
            additional_data (list): 추가 데이터 리스트
            parsing_rules_dict (dict): 파싱 규칙 딕셔너리
        Returns:
            data (tuple): 뉴스 상세 정보 튜플
        """
        if not parsing_rules_dict:
            parsing_rules_dict = self.parsing_rules_dict

        extracted_data = {}
        for element in elements:
            if parsing_rules_dict.get(element):
                # 마지막 규칙을 사용하여 해당 요소를 추출합니다.
                parsing_rule = parsing_rules_dict.get(element)[-1]
                extracted_data[element] = self.extract_element(soup, parsing_rule)
            else:
                err_message = f"PARSING RULES NOT FOUND FOR {element}"
                self.process_err_log_msg(err_message, "extract_news_details")
                extracted_data[element] = None
        return extracted_data

    # 스크랩한 데이터를 데이터베이스에 저장하는 함수
    def check_error(self, news_data: dict, news_url: str) -> None:
        """스크랩한 데이터를 데이터베이스에 저장하는 함수
        Args:
            news_data (dict): 뉴스 데이터
            news_url (str): 뉴스 기사 URL
        """
        # news_data가 None이 아닐 경우에만 저장
        if not news_data:
            self.is_error = True
            err_message = f"CANNOT SCRAP DATA FOR {news_url}"
            self.process_err_log_msg(err_message, "check_error")
        else:
            news_data.content = remove_emojis_and_special_chars(news_data.content)
            self.news_data_list.append(news_data)
            self.mark_as_scraped(news_url)
            success_message = f"NEWS DATA SUCCESSFULLY SCRAPED FOR {news_url}"
            self.process_info_log_msg(success_message, "success")

        # 에러 로그가 있으면 에러 로그 리스트에 추가
        if self.is_error:
            if self.is_duplicated:
                self.session_log['dup_count'] += 1
            else:
                self.session_log['fail_count'] += 1
                self.error_log['error_time'] = self.get_current_time()
                self.error_logs.append(ScrapErrorLog(**self.error_log))

    # 스크랩한 데이터 리스트를 데이터베이스에 저장하는 함수
    def save_news_data_bulk(self, news_data_list: list) -> None:
        """스크랩한 데이터 리스트를 데이터베이스에 저장하는 함수
        Args:
            news_data_list (list): 뉴스 데이터 리스트
        """
        try:
            self.news_db.save_data_bulk(news_data_list, self.scraper_name)
            self.session_log['success_count'] += len(news_data_list)
            success_message = f"{len(news_data_list)} NEWS DATA SAVED FOR {self.scraper_name}"
            self.process_info_log_msg(success_message, "success")
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE SAVING NEWS DATA FOR {self.scraper_name}"
            self.process_err_log_msg(err_message, "save_news_data_bulk", stack_trace, e)

    # 최종 세션 로그 저장 함수
    def finalize_session_log(self) -> None:
        """최종 세션 로그 저장 함수"""
        self.session_log['end_time'] = self.get_current_time()
        try:
            # 세션 로그 저장
            session_log_id = self.scraper_manager_db.save_scrap_session_log(ScrapSessionLog(**self.session_log))
            success_message = f"SESSION LOG SAVED WITH ID: {session_log_id}"
            self.process_info_log_msg(success_message, "success")

            if session_log_id:
                # 에러 로그 세션 로그 id 저장
                for error_log in self.error_logs:
                    error_log.session_log_id = session_log_id

                # 에러 로그 저장
                self.scraper_manager_db.save_scrap_error_logs(self.error_logs)
                success_message = f"ERROR LOGS SAVED FOR SESSION LOG ID: {session_log_id}"
                self.process_info_log_msg(success_message, "success")
                self.error_logs = []    # 에러 로그 리스트 초기화
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = "THERE WAS AN ERROR WHILE SAVING SESSION LOG AND ERROR LOGS"
            log_message = Messages.error_message(err_message, "finalize_session_log", stack_trace, e)
            self.logger.error(log_message)

    # 재시도를 위한 비동기 함수 정의
    async def fetch_url_with_retry(self, session: aiohttp.ClientSession, url: str, retries: int = 3) -> str:
        for attempt in range(retries):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        raise aiohttp.ClientResponseError(response.request_info, response.history, status=response.status, message=response.reason)
            except (aiohttp.ClientConnectorError, aiohttp.ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2)  # 잠시 대기 후 재시도
                else:
                    raise e

    async def scrape_each_news_with_bs(self, news_url, elements, parsing_rules_dict=None):
        try:
            info_message = f"SCRAPING STARTED FOR {news_url}"
            self.process_info_log_msg(info_message, type="info")

            async with aiohttp.ClientSession() as session:
                async with session.get(news_url, headers=self.headers) as response:
                    if response.status == 200:
                        try:
                            text = await response.text()
                        except UnicodeDecodeError:
                            info_message = f"ENCODING ERROR FOR {news_url}"
                            self.process_info_log_msg(info_message, type="info")
                            text = await response.read()
                            if self.media_name in ["dt", "wsobi", "munhwa", "dailypharm", "boannews"]:
                                text = text.decode('euc-kr', 'ignore')
                            elif self.media_name in ["digitalchosun", "news1", "seoul", "newsworks", "businessnews_chosun"]:
                                text = text.decode('utf-8', 'ignore')
                        soup = BeautifulSoup(text, 'html.parser')
                    else:
                        err_message = f"RESPONSE STATUS: {response.status} {response.reason} FOR URL: {news_url}"
                        self.process_err_log_msg(err_message, "scrape_each_news", "", "")
                        return None

            extracted_data = self.extract_news_details(
                soup, elements, parsing_rules_dict=parsing_rules_dict
                )
            return extracted_data

        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE SCRAPING: {news_url}"
            self.process_err_log_msg(err_message, "scrape_each_news", stack_trace, e)
            return None

    async def scrape_each_news_with_trafilatura(self, news_url, elements: list, parsing_rules_dict: dict = None, with_metadata=True):
        extracted_data = {}
        if not parsing_rules_dict:
            parsing_rules_dict = self.parsing_rules_dict
        try:
            info_message = f"SCRAPING STARTED FOR {news_url} WITH TRAFILATURA"
            self.process_info_log_msg(info_message, type="info")

            if self.media_name in ["dt", "wsobi", "munhwa", "dailypharm", "boannews"]:
                response = requests.get(news_url)
                response.encoding = 'euc-kr'
                downloaded = response.text
            else:
                downloaded = fetch_url(
                    news_url,
                    no_ssl=True,
                )
            for element in elements:
                result = bare_extraction(downloaded, with_metadata=with_metadata)
                parsing_rule = parsing_rules_dict.get(element)[-1]
                if parsing_rule:
                    for path in parsing_rule.values():
                        result = result.get(path)
                    extracted_data[element] = result
                else:
                    extracted_data[element] = None
            return extracted_data
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE SCRAPING: {news_url}"
            self.process_err_log_msg(err_message, "scrape_each_news_with_trafilatura", stack_trace, e)
            return None

    @abc.abstractmethod
    def get_news_urls(self, category: str=None) -> Generator[str, None, None]:
        """
        카테고리별 뉴스 URL을 가져오는 추상 메서드.
        서브클래스에서 구현해야 합니다.
        """
        pass

    @abc.abstractmethod
    async def scrape_each_news(self, news_url: str, category: str=None, parsing_rules_dict: dict=None) -> Optional[dict]:
        """
        각 뉴스 기사를 스크랩하는 추상 메서드.
        서브클래스에서 구현해야 합니다.
        """
        pass

    @abc.abstractmethod
    def preprocess_datetime(self, unprocessed_date: str) -> Optional[str]:
        """
        날짜 전처리 함수.
        서브클래스에서 구현해야 합니다.
        """
        pass

    @abc.abstractmethod
    async def scrape_news(self) -> None:
        """
        뉴스 스크래핑을 실행하는 추상 메서드.
        서브클래스에서 구현해야 합니다.
        """
        pass

    @abc.abstractmethod
    def get_feed_entries(self) -> Generator[dict, None, None]:
        """
        피드 엔트리를 가져오는 추상 메서드.
        서브클래스에서 구현해야 합니다.
        """
        pass

    @abc.abstractmethod
    async def scrape_each_feed_entry(self, feed_entry: dict) -> Optional[dict]:
        """
        피드 엔트리를 스크래핑하는 추상 메서드.
        서브클래스에서 구현해야 합니다.
        """
        pass
