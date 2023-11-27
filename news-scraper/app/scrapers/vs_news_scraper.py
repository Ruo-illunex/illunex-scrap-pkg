import asyncio
import datetime
import random
import hashlib
import traceback
import types

import aiohttp
import feedparser
from bs4 import BeautifulSoup

from app.common.core.base_news_scraper import NewsScraper
from app.models_init import EtcNews
from app.scrapers.urls import URLs


class VSNewsScraper(NewsScraper):
    """VS 뉴스 스크래퍼 클래스"""

    def __init__(self, scraper_name: str):
        super().__init__(scraper_name)
        self.interval_time_sleep = 7200
        vs_urls = URLs(scraper_name)
        urls = vs_urls.urls
        self.news_board_url = urls['news_board_url']


    def preprocess_datetime(self, unprocessed_date):
        """날짜 전처리 함수
        Args:
            unprocessed_date (str): 전처리되지 않은 날짜
        Returns:
            str: 전처리된 날짜
        """

        try:
            # 한글 부분을 영어 형식으로 변환
            date_part, time_part = unprocessed_date.replace('년 ', '/').replace('월 ', '/').replace('일 - ', ' - ').split(' - ')

            if '오후' in time_part:
                time_part = time_part.replace('오후 ', '')
                hour, minute = map(int, time_part.split(':'))
                if hour != 12:  # '오후 12시'는 12시로 유지
                    hour += 12
                time_part = f"{hour}:{minute}"
            else:
                time_part = time_part.replace('오전 ', '')
                hour, minute = map(int, time_part.split(':'))
                if hour == 12:  # '오전 12시'는 '00'시로 변경
                    hour = 0
                time_part = f"{hour:02d}:{minute}"

            # 날짜와 시간 부분을 다시 결합
            processed_date = f"{date_part} {time_part}"

            # datetime 객체로 변환
            processed_date = datetime.datetime.strptime(processed_date, "%Y/%m/%d %H:%M")

            return processed_date.strftime("%Y-%m-%d %H:%M:%S")
        
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = "THERE WAS AN ERROR WHILE PROCESSING DATE: {unprocessed_date}"
            self.process_err_log_msg(err_message, "preprocess_datetime", stack_trace, e)
            return None
        
    
    def get_news_urls(self):
        try:
            info_message = f"GETTING NEWS URLS FROM {self.news_board_url}"
            self.process_info_log_msg(info_message, type="info")

            # 피드파서를 이용해서 RSS 피드를 가져옵니다.
            feed = feedparser.parse(self.news_board_url)
            entries = feed.entries

            # 뉴스 기사 URL을 가져옵니다.
            news_urls = [entry.link for entry in entries]

            if len(news_urls) == 0:
                err_message = f"NO NEWS URLS WERE FOUND FROM {self.news_board_url}"
                self.process_err_log_msg(err_message, "get_news_urls", None, None)
                return None
            
            else:
                for news_url in news_urls:
                    yield news_url

        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = "THERE WAS AN ERROR WHILE GETTING NEWS URLS"
            self.process_err_log_msg(err_message, "get_news_urls", stack_trace, e)
            return None


    async def scrape_each_news(self, news_url):
        try:
            info_message = f"SCRAPING STARTED FOR {news_url}"
            self.process_info_log_msg(info_message, type="info")

            async with aiohttp.ClientSession() as session:
                text = await self.fetch_url_with_retry(session, news_url)
                soup = BeautifulSoup(text, 'html.parser')

            extracted_data = self.extract_news_details(soup)

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

            url_md5 = hashlib.md5(news_url.encode()).hexdigest()
            preprocessed_create_date = self.preprocess_datetime(create_date)
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

                news_urls = self.get_news_urls()
                if not isinstance(news_urls, types.GeneratorType):
                    err_message = "GET_NEWS_URLS DOES NOT RETURN A GENERATOR. CHECK THE 'news_board_url' OR THE RETURN VALUE OF FUNCTION 'get_news_urls'"
                    self.process_err_log_msg(err_message, "scrape_news", "", "")
                    return None

                for news_url in news_urls:
                    # 에러 로그 개별 초기화
                    self.is_error = False
                    self.initialize_error_log(news_url)

                    self.session_log['total_records_processed'] += 1

                    await asyncio.sleep(random.randint(1, 5))

                    # 각 뉴스 URL에 대해 세부 정보 스크랩
                    news_data = await self.scrape_each_news(news_url)
                
                    # 스크랩한 데이터를 데이터베이스에 저장
                    # news_data가 None이 아닐 경우에만 저장
                    self.process_news_data_or_error_log(news_data, news_url)
                
                # 최종 세션 로그 저장
                self.finalize_session_log()

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


# VS 뉴스 스크래핑 함수
async def scrape_vs_news():
    """VS 뉴스 스크래핑 함수"""
    portal = "venturesquare"
    scraper = VSNewsScraper(scraper_name=portal)
    await scraper.scrape_news()


if __name__ == "__main__":
    asyncio.run(scrape_vs_news())
