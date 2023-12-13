import asyncio
import random
import hashlib
import traceback
import types

import requests
from bs4 import BeautifulSoup

from app.common.core.base_news_scraper import NewsScraper
from app.models_init import EtcNews
from app.scrapers.urls import URLs
from app.common.core.utils import preprocess_datetime_iso


class StartuptodayNewsScraper(NewsScraper):
    """Startuptoday 뉴스 스크래퍼 클래스"""

    def __init__(self, scraper_name: str):
        super().__init__(scraper_name)
        self.interval_time_sleep = 7200
        startuptoday_urls = URLs(scraper_name)
        urls = startuptoday_urls.urls
        self.news_board_url = urls['news_board_url']
        self.base_url = urls['base_url']


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


    def get_news_urls(self):
        try:
            info_message = f"GETTING NEWS URLS FROM {self.news_board_url}"
            self.process_info_log_msg(info_message, type="info")

            # 뉴스 기사 URL을 가져옵니다.
            response = requests.get(self.news_board_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.select('.thumb')

            if len(links) == 0:
                err_message = f"NO NEWS URLS WERE FOUND FROM {self.news_board_url}"
                self.process_err_log_msg(err_message, "get_news_urls", "", "")
                return None
            
            else:
                for link in links:
                    if '/news/articleView' in link['href']:
                        yield self.base_url.format(link['href'])

        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = "THERE WAS AN ERROR WHILE GETTING NEWS URLS"
            self.process_err_log_msg(err_message, "get_news_urls", stack_trace, e)
            return None


    async def scrape_each_news(self, news_url):
        total_extracted_data = {}
        elements = self.parsing_rules_dict.keys()
        elements_for_bs = []
        elements_for_trafilatura = []

        for element in elements:
            method = self.parsing_rules_dict.get(element)[0]
            if method == "bs":
                elements_for_bs.append(element)
            elif method == "trafilatura":
                elements_for_trafilatura.append(element)

        if elements_for_bs:
            extracted_data_with_bs = await self.scrape_each_news_with_bs(news_url, elements_for_bs)
            if extracted_data_with_bs:
                total_extracted_data.update(extracted_data_with_bs)
        if elements_for_trafilatura:
            extracted_data_with_trafilatura = await self.scrape_each_news_with_trafilatura(news_url, elements_for_trafilatura)
            if extracted_data_with_trafilatura:
                total_extracted_data.update(extracted_data_with_trafilatura)

        title = total_extracted_data.get('title')
        content = total_extracted_data.get('content')
        create_date = total_extracted_data.get('create_date')
        image_url = total_extracted_data.get('image_url')
        media = total_extracted_data.get('media')
        kind = total_extracted_data.get('kind')
            
        # title이나 content, create_date가 없으면 다음 데이터로 넘어갑니다.
        if any([not title, not content, not create_date]):
            none_elements = [element for element in [title, content, create_date] if not element]
            err_message = f"{none_elements} IS EMPTY FOR URL: {news_url}"
            self.process_err_log_msg(err_message, "scrape_each_news", "", "")
            return None

        url_md5 = hashlib.md5(news_url.encode()).hexdigest()
        preprocessed_create_date = self.preprocess_datetime(create_date)
        if self.category_dict.get(self.scraper_name).get(kind):
            kind_id = self.category_dict.get(self.scraper_name).get(kind)
        else:
            kind_id = self.category_dict.get(self.scraper_name).get("etc")

        news_data = EtcNews(
            url=news_url,
            url_md5=url_md5,
            title=title,
            content=content,
            create_date=preprocessed_create_date,
            image_url=image_url,
            portal=self.scraper_name,
            media=media,
            kind=kind_id,
            category="",
            )

        return news_data


    async def scrape_news(self):
        while True:
            try:
                # 세션 로그 초기화
                self.is_error = False
                self.initialize_session_log()

                # 뉴스 데이터 리스트 초기화
                self.news_data_list = []

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

                # 모든 스크래핑이 끝나면 일정 시간 대기
                await asyncio.sleep(self.interval_time_sleep)

            except Exception as e:
                stack_trace = traceback.format_exc()
                err_message = "THERE WAS AN ERROR WHILE SCRAPING NEWS"
                self.process_err_log_msg(err_message, "scrape_news", stack_trace, e)
                await asyncio.sleep(self.retry_delay)


    def get_feed_entries(self):
        pass


    async def scrape_each_feed_entry(self, entry):
        pass


# StartupToday 뉴스 스크래핑 함수
async def scrape_startuptoday_news():
    """StartupToday 뉴스 스크래핑 함수"""
    portal = "startuptoday"
    scraper = StartuptodayNewsScraper(scraper_name=portal)
    await scraper.scrape_news()


if __name__ == "__main__":
    asyncio.run(scrape_startuptoday_news())
