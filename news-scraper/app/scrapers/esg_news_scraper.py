import asyncio
import random
import hashlib
import traceback
import types

import aiohttp
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup

from app.common.core.base_news_scraper import NewsScraper
from app.models_init import EsgNews
from app.scrapers.urls import URLs
from app.common.core.utils import preprocess_datetime_iso


class EsgNewsScraper(NewsScraper):
    """ESG 뉴스 스크래퍼 클래스"""

    def __init__(self, scraper_name: str):
        super().__init__(scraper_name)
        self.interval_time_sleep = 7200
        esg_urls = URLs(scraper_name)
        self.headers = esg_urls.headers
        urls = esg_urls.urls
        self.news_board_url_economy = urls['news_board_url_economy']
        self.news_board_url_social_and_env = urls['news_board_url_social_and_env']
        self.categories = ["economy", "social_and_env"]


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
        
        try:
            raise ValueError(f"Invalid date format: {unprocessed_date}")
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE PROCESSING DATE: {unprocessed_date}"
            self.process_err_log_msg(err_message, "preprocess_datetime", stack_trace, e)
            return None


    def get_news_urls(self, category):
        try:
            if category == 'economy':
                news_board_url = self.news_board_url_economy
            elif category == 'social_and_env':
                news_board_url = self.news_board_url_social_and_env

            info_message = f"GETTING NEWS URLS FROM {news_board_url}"
            self.process_info_log_msg(info_message, type="info")

            response = requests.get(news_board_url)
            # XML 데이터 파싱
            root = ET.fromstring(response.content)

            # 링크 추출
            for item in root.findall('.//item'):
                yield item.find('link').text

        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE GETTING NEWS URLS FROM {news_board_url}"
            self.process_err_log_msg(err_message, "get_news_urls", stack_trace, e)
            return None


    async def scrape_each_news(self, news_url):
        try:
            info_message = f"SCRAPING STARTED FOR {news_url}"
            self.process_info_log_msg(info_message, type="info")

            async with aiohttp.ClientSession(headers=self.headers) as session:
                text = await self.fetch_url_with_retry(session, news_url)
                soup = BeautifulSoup(text, 'html.parser')

            extracted_data = self.extract_news_details(
                soup,
                additional_data=['kind'],
                )

            title = extracted_data.get('title')
            content = extracted_data.get('content')
            create_date = extracted_data.get('create_date')
            image_url = extracted_data.get('image_url')
            media = extracted_data.get('media')
            kind = extracted_data.get('kind')

            # title이나 content가 없으면 다음 데이터로 넘어갑니다.
            if not title or not content:
                err_message = f"TITLE OR CONTENT IS EMPTY FOR URL: {news_url}"
                self.process_err_log_msg(err_message, "scrape_each_news", "", "")
                return None

            url_md5 = hashlib.md5(news_url.encode()).hexdigest()
            preprocessed_create_date = self.preprocess_datetime(create_date)
            if self.category_dict.get(self.scraper_name).get(kind):
                kind_id = self.category_dict.get(self.scraper_name).get(kind)
            else:
                kind_id = self.category_dict.get(self.scraper_name).get("etc")

            news_data = EsgNews(
                url=news_url,
                url_md5=url_md5,
                title=title,
                content=content,
                create_date=preprocessed_create_date,
                image_url=image_url,
                portal=self.scraper_name,
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


    async def scrape_news(self):
        while True:
            try:
                # 세션 로그 초기화
                self.is_error = False
                self.initialize_session_log()

                # 뉴스 데이터 리스트 초기화
                self.news_data_list = []

                # 카테고리별 뉴스 URL을 가져옵니다.
                for category in self.categories:
                    news_urls = self.get_news_urls(category)
                    if not isinstance(news_urls, types.GeneratorType):
                        err_message = "GET_NEWS_URLS DOES NOT RETURN A GENERATOR. CHECK THE 'news_board_url' OR THE RETURN VALUE OF FUNCTION 'get_news_urls'"
                        self.process_err_log_msg(err_message, "scrape_news", "", "")
                        continue

                    for news_url in news_urls:
                        # 에러 로그 개별 초기화
                        self.is_error = False
                        self.initialize_error_log(news_url)

                        self.session_log['total_records_processed'] += 1

                        await asyncio.sleep(random.randint(1, 2))

                        # 각 뉴스 URL에 대해 세부 정보 스크랩
                        news_data = await self.scrape_each_news(
                            news_url,
                            )

                        # 뉴스 데이터에 에러가 있으면, 에러 로그를 append하고, 그렇지 않으면 뉴스 데이터를 리스트에 추가
                        self.check_error(news_data, news_url)

                # 뉴스 데이터베이스에 한 번에 저장
                self.save_news_data_bulk(self.news_data_list, self.scraper_name)
                
                # 최종 세션 로그 저장
                self.finalize_session_log()

                # 모든 카테고리에 대한 스크래핑이 끝나면 일정 시간 대기
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


# ESG 뉴스 스크래핑 함수
async def scrape_esg_news():
    portal = "esg_economy"
    esg_news_scraper = EsgNewsScraper(scraper_name=portal)
    await esg_news_scraper.scrape_news()


if __name__ == "__main__":
    asyncio.run(scrape_esg_news())
