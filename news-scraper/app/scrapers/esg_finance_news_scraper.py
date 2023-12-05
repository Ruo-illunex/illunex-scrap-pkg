import asyncio
import random
import hashlib
import traceback
import types
import datetime
import glob
import os

import aiohttp
from bs4 import BeautifulSoup
import pandas as pd

from app.common.core.base_news_scraper import NewsScraper
from app.models_init import EsgNews
from app.scrapers.urls import URLs
from app.scrapers.esg_finance_hub_scraper import EsgFinanceHubScraper
from app.common.core.utils import preprocess_datetime_iso, preprocess_datetime_compact, preprocess_datetime_rfc2822, preprocess_datetime_standard, preprocess_datetime_standard_without_seconds, preprocess_datetime_korean_without_seconds, preprocess_datetime_period_without_seconds, preprocess_date_period
from app.config.settings import FILE_PATHS
from app.common.core.utils import load_yaml


class EsgfinanceNewsScraper(NewsScraper):
    """ESG FINANCE 뉴스 스크래퍼 클래스"""

    def __init__(self, scraper_name: str):
        super().__init__(scraper_name)
        self.interval_time_sleep = 7200
        esgfinance_urls = URLs(self.scraper_name)
        self.headers = esgfinance_urls.headers
        urls = esgfinance_urls.urls
        self.news_board_url = urls['news_board_url']
        self.esg_finance_hub_scraper = EsgFinanceHubScraper(scraper_name=self.scraper_name)
        self.media = load_yaml(FILE_PATHS.get('esg_finance_media')).get('media')
        self.media_name = None


    def get_all_links_and_save_to_csv(self):
        """모든 링크를 가져와서 CSV 파일에 저장하는 함수"""
        try:
            self.esg_finance_hub_scraper.get_all_links_and_save_to_csv()
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = "THERE WAS AN ERROR WHILE GETTING ALL LINKS AND SAVING TO CSV.\nCHECK THE ESG FINANCE HUB SCRAPER LOGS FOR MORE DETAILS"
            self.process_err_log_msg(err_message, "get_all_links_and_save_to_csv", stack_trace, e)


    def preprocess_datetime(self, unprocessed_date):
        """날짜 전처리 함수
        Args:
            unprocessed_date (str): 전처리되지 않은 날짜
        Returns:
            str: 전처리된 날짜
        """

        processed_date = preprocess_datetime_iso(unprocessed_date)
        if processed_date:
            return processed_date
        
        processed_date = preprocess_datetime_compact(unprocessed_date)
        if processed_date:
            return processed_date
        
        processed_date = preprocess_datetime_rfc2822(unprocessed_date)
        if processed_date:
            return processed_date
        
        processed_date = preprocess_datetime_standard(unprocessed_date)
        if processed_date:
            return processed_date
        
        processed_date = preprocess_datetime_standard_without_seconds(unprocessed_date)
        if processed_date:
            return processed_date
        
        processed_date = preprocess_datetime_korean_without_seconds(unprocessed_date)
        if processed_date:
            return processed_date

        processed_date = preprocess_datetime_period_without_seconds(unprocessed_date)
        if processed_date:
            return processed_date
        
        processed_date = preprocess_date_period(unprocessed_date)
        if processed_date:
            return processed_date

        try:
            raise ValueError(f"Invalid date format: {unprocessed_date}")
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE PROCESSING DATE: {unprocessed_date}"
            self.process_err_log_msg(err_message, "preprocess_datetime", stack_trace, e)
            return None


    def get_news_urls(self):
        try:
            for link in self.esg_finance_hub_scraper.get_first_page_links():
                self.media_name = self.media.get(link.split('/')[2])
                self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name=self.media_name)
                yield link
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE GETTING NEWS URLS FROM {self.news_board_url}\nCHECK THE ESG FINANCE HUB SCRAPER LOGS FOR MORE DETAILS"
            self.process_err_log_msg(err_message, "get_news_urls", stack_trace, e)
            return None


    def get_all_news_urls(self):
        try:
            # CSV 파일 경로
            file_path = FILE_PATHS.get(f'{self.scraper_name}_links_csv')
            file_list = glob.glob(file_path)

            # CSV 파일이 존재하는 경우
            if file_list:
                file_list.sort(key=lambda x: os.path.splitext(os.path.basename(x))[0][-14:])
                latest_file = file_list[-1]
                df = pd.read_csv(latest_file)
                df.columns = ['page', 'url']
                df = df.drop_duplicates(subset=['url'], keep='first')
                for url in df['url'].tolist():
                    self.media_name = self.media.get(url.split('/')[2])
                    self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name=self.media_name)
                    yield url
            # CSV 파일이 존재하지 않는 경우
            else:
                info_message = f"CSV FILE DOES NOT EXIST FOR {self.scraper_name}"
                self.process_info_log_msg(info_message, type="info")

                self.get_all_links_and_save_to_csv()
                return None
        
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE GETTING ALL NEWS URLS FROM {self.news_board_url}\nCHECK THE ESG FINANCE HUB SCRAPER LOGS FOR MORE DETAILS"
            self.process_err_log_msg(err_message, "get_all_news_urls", stack_trace, e)
            return None


    async def scrape_each_news(self, news_url):
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
                            if self.media_name in ["dt", "wsobi", "munhwa"]:
                                text = text.decode('euc-kr', 'ignore')
                            elif self.media_name in ["digitalchosun", "news1", "seoul", "newsworks"]:
                                text = text.decode('utf-8', 'ignore')
                        soup = BeautifulSoup(text, 'html.parser')
                    else:
                        err_message = f"RESPONSE STATUS: {response.status} {response.reason} FOR URL: {news_url}"
                        self.process_err_log_msg(err_message, "scrape_each_news", "", "")
                        return None

            extracted_data = self.extract_news_details(
                soup,
                )

            title = extracted_data.get('title')
            content = extracted_data.get('content')
            create_date = extracted_data.get('create_date')
            image_url = extracted_data.get('image_url')
            media = extracted_data.get('media')

            # title이나 content가 없으면 다음 데이터로 넘어갑니다.
            if not title or not content:
                err_message = f"TITLE OR CONTENT IS EMPTY FOR URL: {news_url}"
                self.process_err_log_msg(err_message, "scrape_each_news", "", "")
                return None

            if self.media_name == "dt":
                image_url = f"https:{image_url}"

            if self.media_name in ["wsobi", "paxetv"]:
                create_date = create_date.split('승인')[-1].strip()

            if self.media_name in ["digitalchosun", "dnews"]:
                create_date = create_date[5:]

            if self.media_name == "bizchosun":
                create_date = create_date.split('.')[0]
            
            if self.media_name == "newstong":
                create_date = create_date.split('|')[-1].strip()
            
            if self.media_name == "metroseoul":
                create_date = create_date.split('ㅣ')[-1].strip()
            
            if self.media_name == "mediapen":
                create_date = create_date.split(' | ')[0].strip()
            
            if self.media_name == "ceoscoredaily":
                image_url = f"https://www.ceoscoredaily.com{image_url}"

            if self.media_name in ["guardian", "news_yahoo", "uk_news_yahoo", "bbc"]:
                create_date = create_date.split('.')[0]
            
            if self.media_name == "news2day":
                create_date = create_date.split(' : ')[-1].strip()

            if self.media_name == "busan":
                create_date = create_date.replace('[', '').replace(']', '')

            if self.media_name == "munhwa":
                create_date = create_date.replace('입력 ', '').strip()
            
            if self.media_name == "news_kbs":
                create_date = create_date.replace('입력 ', '').replace('(', '').replace(')', '').strip()
            
            if self.media_name == "asiatime":
                create_date = create_date.split('입력 ')[-1].split(' 수정')[0].strip()

            if self.media_name == "economist":
                create_date = create_date.replace('[이코노미스트] 입력 ', '')
            
            if self.media_name == "naeil":
                create_date = create_date.replace(' 게재', '')

            url_md5 = hashlib.md5(news_url.encode()).hexdigest()
            preprocessed_create_date = self.preprocess_datetime(create_date)
            kind_id = self.category_dict.get(self.scraper_name).get("etc")

            news_data = EsgNews(
                url=news_url,
                url_md5=url_md5,
                title=title,
                content=content,
                create_date=preprocessed_create_date,
                image_url=image_url,
                portal='esg_finance',
                media=media,
                kind=kind_id,
                category="ESG",
                esg_analysis="",
                )

            return news_data

        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE SCRAPING: {news_url}"
            self.process_err_log_msg(err_message, "scrape_each_news", stack_trace, e)
            return None


    async def scrape_news(self, get_all_news_urls=False):
        while True:
            try:
                # 세션 로그 초기화
                self.is_error = False
                self.initialize_session_log()

                # 뉴스 데이터 리스트 초기화
                self.news_data_list = []

                if get_all_news_urls:
                    news_urls = self.get_all_news_urls()
                else:
                    news_urls = self.get_news_urls()

                if not isinstance(news_urls, types.GeneratorType):
                    err_message = "GET_NEWS_URLS DOES NOT RETURN A GENERATOR. CHECK THE 'news_board_url' OR THE RETURN VALUE OF FUNCTION 'get_news_urls'"
                    self.process_err_log_msg(err_message, "scrape_news", "", "")
                    return None

                for news_url in news_urls:
                    news_data = None
                    # 에러 로그 개별 초기화
                    self.is_error = False
                    self.initialize_error_log(news_url)

                    self.session_log['total_records_processed'] += 1
                    if not self.is_already_scraped(news_url):
                        await asyncio.sleep(random.randint(1, 5))

                        # 각 뉴스 URL에 대해 세부 정보 스크랩
                        news_data = await self.scrape_each_news(news_url)
                    else:
                        err_message = f"NEWS ALREADY EXISTS IN DATABASE: {news_url}"
                        self.process_err_log_msg(err_message, "scrape_news", "", "")

                    # 뉴스 데이터에 에러가 있으면, 에러 로그를 append하고, 그렇지 않으면 뉴스 데이터를 리스트에 추가
                    self.check_error(news_data, news_url)

                # 뉴스 데이터베이스에 한 번에 저장
                self.save_news_data_bulk(self.news_data_list)
                
                # 최종 세션 로그 저장
                self.finalize_session_log()

                if get_all_news_urls:
                    success_message = f"SCRAPING COMPLETED FOR {self.scraper_name} WITH {self.session_log['total_records_processed']} RECORDS"
                    self.process_success_log_msg(success_message, "scrape_news")
                    break

                # 모든 스크래핑이 끝나면 일정 시간 대기
                await asyncio.sleep(self.interval_time_sleep)

            except Exception as e:
                stack_trace = traceback.format_exc()
                err_message = "THERE WAS AN ERROR WHILE SCRAPING NEWS"
                self.process_err_log_msg(err_message, "scrape_news", stack_trace, e)
                await asyncio.sleep(60)


    def get_feed_entries(self):
        pass


    async def scrape_each_feed_entry(self, entry):
        pass


# ESG FINANCE 뉴스 스크래핑
async def scrape_esg_finance_news(get_all_news_urls=False):
    """ESG FINANCE 뉴스를 스크래핑하는 함수"""
    portal = "esg_finance_hub"
    esgfinance_news_scraper = EsgfinanceNewsScraper(scraper_name=portal)
    await esgfinance_news_scraper.scrape_news(get_all_news_urls=get_all_news_urls)

if __name__ == "__main__":
    asyncio.run(scrape_esg_finance_news())
