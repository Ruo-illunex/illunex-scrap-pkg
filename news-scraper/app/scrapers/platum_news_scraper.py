import asyncio
import random
import hashlib
import traceback
import types
import email.utils

import feedparser
from bs4 import BeautifulSoup

from app.common.core.base_news_scraper import NewsScraper
from app.models_init import EtcNews
from app.scrapers.urls import URLs
from app.common.core.utils import preprocess_datetime_rfc2822


class PlatumNewsScraper(NewsScraper):
    """Platum 뉴스 스크래퍼 클래스"""

    def __init__(self, scraper_name: str):
        super().__init__(scraper_name)
        self.interval_time_sleep = 7200
        platum_urls = URLs(scraper_name)
        self.headers = platum_urls.headers
        urls = platum_urls.urls
        self.news_board_url = urls['news_board_url']


    def preprocess_datetime(self, unprocessed_date):
        """날짜 전처리 함수
        Args:
            unprocessed_date (str): 전처리되지 않은 날짜
        Returns:
            str: 전처리된 날짜
        """
            
        processed_date = preprocess_datetime_rfc2822(unprocessed_date)
        if processed_date:
            return processed_date
        else:
            try:
                raise ValueError(f"Invalid date format: {unprocessed_date}")
            except Exception as e:
                stack_trace = traceback.format_exc()
                err_message = f"THERE WAS AN ERROR WHILE PROCESSING DATE: {unprocessed_date}"
                self.process_err_log_msg(err_message, "preprocess_datetime", stack_trace, e)
                return None


    def get_feed_entries(self):
        try:
            info_message = f"GETTING NEWS URLS FROM {self.news_board_url}"
            self.process_info_log_msg(info_message, type="info")

            # 피드파서를 이용해서 RSS 피드를 가져옵니다.
            feed = feedparser.parse(self.news_board_url)
            entries = feed.entries

            if len(entries) == 0:
                err_message = f"NO FEED ENTRIES WERE FOUND FROM {self.news_board_url}"
                self.process_err_log_msg(err_message, "get_feed_entries", None, None)
                return None
            
            else:
                for entry in entries:
                    yield entry

        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = "THERE WAS AN ERROR WHILE GETTING FEED ENTRIES"
            self.process_err_log_msg(err_message, "get_feed_entries", stack_trace, e)
            return None


    async def scrape_each_feed_entry(self, entry):
        try:
            # 기사 URL을 가져옵니다.
            url = entry.link
            info_message = f"SCRAPING STARTED FOR {url}"
            self.process_info_log_msg(info_message, type="info")

            title = entry.title
            create_date = entry.published
            content_html = entry.content[0].value
            kind = entry.tags[0].term
            media = "platum"

            # 기사 HTML을 가져옵니다.
            soup = BeautifulSoup(content_html, 'html.parser')
            content = soup.get_text()
            extracted_data = self.extract_news_details(soup)
            image_url = extracted_data.get('image_url')

            # title이나 content가 없으면 다음 데이터로 넘어갑니다.
            if not title or not content:
                err_message = f"TITLE OR CONTENT IS EMPTY FOR URL: {url}"
                self.process_err_log_msg(err_message, "scrape_each_feed_entry", "", "")
                return None

            url_md5 = hashlib.md5(url.encode()).hexdigest()
            preprocessed_create_date = self.preprocess_datetime(create_date)
            if self.category_dict.get(self.scraper_name).get(kind):
                kind_id = self.category_dict.get(self.scraper_name).get(kind)
            else:
                kind_id = self.category_dict.get(self.scraper_name).get("etc")

            news_data = EtcNews(
                url=url,
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

        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE SCRAPING: {url}"
            self.process_err_log_msg(err_message, "scrape_each_feed_entry", stack_trace, e)
            return None


    async def scrape_news(self):
        while True:
            try:
                # 세션 로그 초기화
                self.is_error = False
                self.initialize_session_log()

                # 뉴스 데이터 리스트 초기화
                self.news_data_list = []

                # 피드 엔트리를 가져옵니다.
                feed_entries = self.get_feed_entries()
                if not isinstance(feed_entries, types.GeneratorType):
                    err_message = "FEED ENTRIES IS NOT A GENERATOR"
                    self.process_err_log_msg(err_message, "scrape_news", None, None)
                    return None
                
                # 피드 엔트리를 순회하며 기사를 스크랩합니다.
                for entry in feed_entries:
                    news_data = None
                    news_url = entry.link

                    # 에러 로그 개별 초기화
                    self.is_error = False
                    self.initialize_error_log(news_url)

                    self.session_log['total_records_processed'] += 1
                    if not self.is_already_scraped(news_url):
                        await asyncio.sleep(random.randint(1, 5))

                        # 각 뉴스 URL에 대해 세부 정보 스크랩
                        news_data = await self.scrape_each_feed_entry(entry)
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


    def get_news_urls(self):
        pass


    async def scrape_each_news(self, news_url):
        pass


# Platum 뉴스 스크래핑 함수
async def scrape_platum_news():
    portal = "platum"
    scraper = PlatumNewsScraper(scraper_name=portal)
    await scraper.scrape_news()


if __name__ == "__main__":
    asyncio.run(scrape_platum_news())
