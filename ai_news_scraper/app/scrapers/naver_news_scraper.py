import asyncio
import datetime
import random
import traceback
import types
import re

import requests
from bs4 import BeautifulSoup

from app.common.core.base_news_scraper import NewsScraper
from app.models_init import NaverNews
from app.scrapers.urls import URLs
from app.common.core.utils import *


class NaverNewsScraper(NewsScraper):
    """Naver 뉴스 스크래퍼 클래스"""

    def __init__(self, scraper_name: str):
        super().__init__(scraper_name)
        self.interval_time_sleep = 120
        naver_urls = URLs(scraper_name)
        urls = naver_urls.urls
        self.news_board_url = urls['news_board_url']
        
        # naver는 naver 일반 뉴스 외에 sports.naver.com도 있습니다.
        # naver_sports 파싱 규칙 추가
        # 한 개 이상의 파싱 규칙을 사용할 경우, self.parsing_rules_dict2에 추가합니다.
        self.parsing_rules_dict2 = self.get_parsing_rules_dict(f"{self.scraper_name}_sports")
        self.all_parsing_rules_dicts = [self.parsing_rules_dict, self.parsing_rules_dict2]


    def preprocess_datetime_custom(self, date_str):
        """사용자 정의 날짜 형식 처리"""
        try:
            matched = re.search(r'기사입력 (\d{4}\.\d{2}\.\d{2}\.) (오전|오후) (\d{2}:\d{2})', date_str)
            if matched:
                date_part = matched.group(1).strip('.')
                am_pm = matched.group(2)
                time_part = matched.group(3)

                hour, minute = map(int, time_part.split(':'))
                if am_pm == '오후' and hour < 12:
                    hour += 12

                final_date_str = f"{date_part} {hour:02d}:{minute:02d}"
                return datetime.datetime.strptime(final_date_str, "%Y.%m.%d %H:%M")
            return None
        except ValueError:
            return None


    def preprocess_datetime(self, unprocessed_date):
        """날짜 전처리 함수"""
        # 각 형식에 대해 순차적으로 시도
        processed_date = preprocess_datetime_standard(unprocessed_date)
        if processed_date:
            return processed_date

        processed_date = preprocess_datetime_compact(unprocessed_date)
        if processed_date:
            return processed_date
        
        processed_date = preprocess_datetime_compact(unprocessed_date)
        if processed_date:
            return processed_date

        processed_date = self.preprocess_datetime_custom(unprocessed_date)
        if processed_date:
            return processed_date

        # 모든 형식이 실패한 경우, 로그 처리
        try:
            raise ValueError(f"Invalid date format: {unprocessed_date}")
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE PROCESSING DATE: {unprocessed_date}"
            self.process_err_log_msg(err_message, "preprocess_datetime", stack_trace, e)
            return None


    def get_news_urls(self, category):
        try:
            url = self.news_board_url.format(category)

            info_message = f"GETTING NEWS URLS FROM {url}"
            self.process_info_log_msg(info_message, type="info")

            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 뉴스 기사 URL을 가져옵니다.
            links = soup.find_all('a', class_='nclicks(fls.list)', href=True)
            news_urls = [link['href'] for link in links]

            if len(news_urls) == 0:
                err_message = f"NO NEWS URLS WERE FOUND FROM {url}"
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


    async def scrape_each_news(self, news_url, category, parsing_rules_dict=None):
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
            extracted_data_with_bs = await self.scrape_each_news_with_bs(news_url, elements_for_bs, parsing_rules_dict=parsing_rules_dict)
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

        # title이나 content, create_date가 없으면 다음 데이터로 넘어갑니다.
        if any([not title, not content, not create_date]):
            none_elements = [element for element in [title, content, create_date] if not element]
            err_message = f"{none_elements} IS EMPTY FOR URL: {news_url}"
            self.process_err_log_msg(err_message, "scrape_each_news", "", "")
            return None

        url_md5 = self.generate_md5(news_url)
        create_date = self.preprocess_datetime(create_date)
        if self.category_dict.get(self.scraper_name).get(category):
            kind_id = self.category_dict.get(self.scraper_name).get(category)
        else:
            kind_id = self.category_dict.get(self.scraper_name).get("etc")

        news_data = NaverNews(
            url=news_url,
            url_md5=url_md5,
            title=title,
            content=content,
            create_date=create_date,
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

                # 카테고리별 뉴스 URL을 가져옵니다.
                for category in self.categories:
                    news_urls = self.get_news_urls(category)
                    if not isinstance(news_urls, types.GeneratorType):
                        err_message = "GET_NEWS_URLS DOES NOT RETURN A GENERATOR. CHECK THE 'news_board_url' OR THE RETURN VALUE OF FUNCTION 'get_news_urls'"
                        self.process_err_log_msg(err_message, "scrape_news", "", "")
                        continue

                    for news_url in news_urls:
                        # 마지막 스크래퍼 여부 초기화
                        scraper_cursor = 0
                        news_data = None

                        # 에러 로그 개별 초기화
                        self.is_error = False
                        self.initialize_error_log(news_url)

                        self.session_log['total_records_processed'] += 1
                        if not self.is_already_scraped(news_url):
                            await asyncio.sleep(random.randint(1, 2))
                            while not news_data and scraper_cursor < len(self.all_parsing_rules_dicts):
                                current_parsing_rule = self.all_parsing_rules_dicts[scraper_cursor]

                                news_data = await self.scrape_each_news(
                                    news_url,
                                    category,
                                    current_parsing_rule
                                    )

                                # 스크랩한 데이터가 없고, 마지막 스크래퍼인 경우 > 에러
                                scraper_cursor += 1
                                if not news_data and scraper_cursor == len(self.all_parsing_rules_dicts):
                                    err_message = f"NEWS DATA IS EMPTY FOR URL: {news_url}"
                                    self.process_err_log_msg(err_message, "scrape_news", "", "")

                        else:
                            err_message = f"NEWS ALREADY EXISTS IN DATABASE: {news_url}"
                            self.process_err_log_msg(err_message, "scrape_news", "", "")

                        # 뉴스 데이터에 에러가 있으면, 에러 로그를 append하고, 그렇지 않으면 뉴스 데이터를 리스트에 추가
                        self.check_error(news_data, news_url)

                # 뉴스 데이터베이스에 한 번에 저장
                self.save_news_data_bulk(self.news_data_list)

                # 최종 세션 로그 저장
                self.finalize_session_log()

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

# 네이버 뉴스 스크래핑 함수
async def scrape_naver_news():
    """네이버 뉴스 스크래핑 함수"""
    portal = "naver"
    scraper = NaverNewsScraper(scraper_name=portal)
    await scraper.scrape_news()


if __name__ == "__main__":
    asyncio.run(scrape_naver_news())
