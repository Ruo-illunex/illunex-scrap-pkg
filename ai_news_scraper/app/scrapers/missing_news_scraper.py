import asyncio
import random
import hashlib
import traceback
import types
import time
import datetime

import requests
import aiohttp
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

from app.common.core.base_news_scraper import NewsScraper
from app.models_init import EsgNews
from app.common.core.utils import *
from app.config.settings import FILE_PATHS
from app.common.core.utils import load_yaml, normal_text, truncate_content


class MissingNewsScraper(NewsScraper):
    """Missing 뉴스 스크래퍼 클래스"""

    def __init__(self, scraper_name: str, df: pd.DataFrame, file_name: str):
        """생성자
        Args:
            scraper_name (str): 스크래퍼 이름
            df (pd.DataFrame): csv 파일을 읽은 DataFrame
            file_name (str): csv 파일 이름
        """
        super().__init__(scraper_name)
        self._df = df
        self._file_path = FILE_PATHS.get('data')+'/'+file_name
        self.media_name = None
        self.type1 = load_yaml(FILE_PATHS.get('esg_finance_media')).get('type1')
        self.type2 = load_yaml(FILE_PATHS.get('esg_finance_media')).get('type2')
        self.type3 = load_yaml(FILE_PATHS.get('esg_finance_media')).get('type3')
        self.type4 = load_yaml(FILE_PATHS.get('esg_finance_media')).get('type4')
        self.media = load_yaml(FILE_PATHS.get('esg_finance_media')).get('media')

    def preprocess_datetime(self, unprocessed_date: str) -> str:
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

        processed_date = preprocess_datetime_compact_with_seperator(unprocessed_date)
        if processed_date:
            return processed_date

        processed_date = preprocess_datetime_rfc2822(unprocessed_date)
        if processed_date:
            return processed_date

        processed_date = preprocess_datetime_rfc3339(unprocessed_date)
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

        processed_date = preprocess_datetime_eng_without_seconds(unprocessed_date)
        if processed_date:
            return processed_date

        try:
            raise ValueError(f"Invalid date format: {unprocessed_date}")
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE PROCESSING DATE: {unprocessed_date}"
            self.process_err_log_msg(err_message, "preprocess_datetime", stack_trace, e)
            return None

    def _cal_date_range(self, dt_str: str) -> tuple:
        """기준 날짜의 한달 전과 한달 후를 구하는 함수
        Args:
            dt_str (str): 기준 날짜
        Returns:
            tuple: 한달 전, 한달 후 날짜
        """
        # 기준 날짜의 한달 전과 한달 후를 구한다.
        # ex) 2017-01-01 -> 2016.12.01, 2017.02.01
        dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d')
        prev = dt - datetime.timedelta(days=30)
        next = dt + datetime.timedelta(days=30)
        return prev.strftime('%Y.%m.%d'), next.strftime('%Y.%m.%d')

    def get_news_urls(self, word: str, ds: str, de: str) -> str:
        """네이버 뉴스를 검색하는 함수
        Args:
            word (str): 검색어
            ds (str): 검색 시작 날짜
            de (str): 검색 종료 날짜
        Returns:
            str: 검색 결과의 뉴스 링크
        """
        try:
            url = "https://search.naver.com/search.naver"
            headers = {'User-Agent': 'Mozila/5.0'}
            params = {
                'where': 'news',
                'query': word,
                'sm': 'tab_opt',
                'sort': 0,
                'photo': 0,
                'field': 0,
                'pd': 3,
                'ds': ds,
                'de': de,
            }
            while True:
                time.sleep(random.randint(1, 5))
                resp = requests.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    html = resp.text
                    soup = BeautifulSoup(html, 'html.parser')
                    news_items = soup.select('.list_news > li')
                    for item in news_items:
                        link = item.select_one('.news_tit')['href']

                        domain = link.split('/')[2]
                        if domain in self.type1:
                            self.media_name = self.type1.get(domain)
                            self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name='esg_finance_hub1')
                        elif domain in self.type2:
                            self.media_name = self.type2.get(domain)
                            self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name='esg_finance_hub2')
                        elif domain in self.type3:
                            self.media_name = self.type3.get(domain)
                            self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name='esg_finance_hub3')
                        elif domain in self.type4:
                            self.media_name = self.type4.get(domain)
                            self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name='esg_finance_hub4')
                        elif domain in self.media:
                            self.media_name = self.media.get(domain)
                            self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name=self.media_name)
                        else:
                            self.media_name = 'Not Registered'
                            self.parsing_rules_dict = {}
                        yield link
                    break
                elif resp.status_code == 403:
                    err_message = f"status code: {resp.status_code} / Blocked by Naver. Retrying in 10 minutes..."
                    self.process_err_log_msg(err_message=err_message, function_name='get_news_urls')
                    time.sleep(600)
                    continue
                else:
                    err_message = f"status code: {resp.status_code}"
                    self.process_err_log_msg(err_message=err_message, function_name='get_news_urls')
                    return
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = "THERE WAS AN ERROR WHILE GETTING LINKS FROM NAVER"
            self.process_err_log_msg(err_message, "get_news_urls", stack_trace, e)
            return

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

        with_metadata = True
        if self.media_name in ["kidd"]:
            with_metadata = False
        if elements_for_bs:
            extracted_data_with_bs = await self.scrape_each_news_with_bs(news_url, elements_for_bs)
            if extracted_data_with_bs:
                total_extracted_data.update(extracted_data_with_bs)
        if elements_for_trafilatura:
            extracted_data_with_trafilatura = await self.scrape_each_news_with_trafilatura(news_url, elements_for_trafilatura, with_metadata=with_metadata)
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

        if self.media_name in ["dt", "metroseoul"]:
            image_url = f"https:{image_url}"

        if self.media_name in ["paxetv"]:
            create_date = create_date.split('승인')[-1].strip()

        if self.media_name in ["digitalchosun_dizzo", "dnews", "thevaluenews", "kidd"]:
            create_date = create_date[5:]

        if self.media_name == "metroseoul":
            create_date = create_date.split('ㅣ')[-1].strip()

        if self.media_name == "mediapen":
            create_date = create_date.split('|')[0].strip()

        if self.media_name == "ceoscoredaily":
            image_url = f"https://www.ceoscoredaily.com{image_url}"

        if self.media_name in ["theguardian", "news_yahoo", "uk_news_yahoo", "sg_news_yahoo", "bbc", "ca_news_yahoo", "au_news_yahoo", "nz_news_yahoo"]:
            create_date = create_date.split('.')[0]

        if self.media_name == "the bell":
            create_date = create_date.replace('공개 ', '').strip()

        if self.media_name == "kjdaily":
            create_date = create_date[:11].replace(' ', '') + create_date[14:]

        if self.media_name == "jnilbo":
            create_date = create_date.split(' : ')[-1][:11].replace(' ', '') + create_date.split(' : ')[-1][14:]

        if self.media_name in ["news_mtn", "wowtv", "cnn"]:
            create_date = create_date[:-1]

        if self.media_name in ["busan", "news2day", "nongmin", "dt"]:
            create_date = create_date.split(': ')[-1].strip()

        if self.media_name in ["businessnews_chosun", "taxtimes", "youthdaily", "hellot"]:
            create_date = create_date.split('등록 ')[-1].strip()

        if self.media_name == "weekly_cnbnews":
            create_date = create_date.split('⁄ ')[-1].strip()

        if self.media_name == "kwnews":
            image_url = f"https://www.kwnews.co.kr{image_url}"

        if self.media_name == "busan":
            image_url = f"https://www.busan.com{image_url}"

        if self.media_name in ["kwnews"]:
            create_date = create_date.replace('[', '').replace(']', '')

        if self.media_name in ["newstong"]:
            create_date = create_date.split('\t')[-1].strip()

        if self.media_name == "naeil":
            create_date = create_date.replace(' 게재', '').strip()

        if self.media_name in ["munhwa", "lak", "boannews", "kyeongin"]:
            create_date = create_date.replace('입력 ', '').strip()

        if self.media_name == "cnbnews":
            create_date = create_date.split('\xa0')[-1].strip()

        if self.media_name == "asiatime":
            create_date = create_date.split('입력 ')[-1].split(' 수정')[0].strip()

        # if self.media_name == "biz_chosun":
        #     create_date = create_date.split('.')[0]

        # if self.media_name == "news_kbs":
        #     create_date = create_date.replace('입력 ', '').replace('(', '').replace(')', '').strip()

        # if self.media_name == "economist":
        #     create_date = create_date.replace('[이코노미스트] 입력 ', '')

        url_md5 = hashlib.md5(news_url.encode()).hexdigest()
        preprocessed_create_date = self.preprocess_datetime(create_date)
        norm_title = normal_text(title)
        content = truncate_content(content)

        news_data = EsgNews(
            url=news_url,
            url_md5=url_md5,
            title=title,
            content=content,
            create_date=preprocessed_create_date,
            image_url=image_url,
            portal='naver',
            media=media,
            kind="999999",
            category="MISSING_NEWS",
            esg_analysis="",
            norm_title=norm_title,
            )
        return news_data

    async def scrape_news(self):
        """뉴스 스크래핑 함수"""
        try:
            for corp, date, investor in zip(self._df['기업명'], self._df['일자'], self._df['투자사']):
                # 세션 로그 초기화
                self.initialize_session_log()

                ds, de = self._cal_date_range(date)
                if investor is not np.nan:
                    investors = investor.split(',')
                    for inv in investors:
                        word = f'{corp} + {inv.strip()}'
                        for news_url in self.get_news_urls(word, ds, de):
                            news_data = None
                            self.initialize_error_log(news_url)
                            self.session_log['total_records_processed'] += 1
                            if not self.is_already_scraped(news_url):
                                await asyncio.sleep(random.randint(1, 5))
                                news_data = await self.scrape_each_news(news_url)
                            else:
                                self.is_duplicated = True
                                err_message = f"NEWS ALREADY EXISTS IN DATABASE: {news_url}"
                                self.process_err_log_msg(err_message, "scrape_news", "", "")

                            # 뉴스 데이터에 에러가 있으면, 에러 로그를 append하고, 그렇지 않으면 뉴스 데이터를 리스트에 추가
                            self.check_error(news_data, news_url)

                for news_url in self.get_news_urls(corp, ds, de):
                    news_data = None
                    self.initialize_error_log(news_url)
                    self.session_log['total_records_processed'] += 1
                    if not self.is_already_scraped(news_url):
                        await asyncio.sleep(random.randint(1, 5))
                        news_data = await self.scrape_each_news(news_url)
                    else:
                        self.is_duplicated = True
                        err_message = f"NEWS ALREADY EXISTS IN DATABASE: {news_url}"
                        self.process_err_log_msg(err_message, "scrape_news", "", "")

                    # 뉴스 데이터에 에러가 있으면, 에러 로그를 append하고, 그렇지 않으면 뉴스 데이터를 리스트에 추가
                    self.check_error(news_data, news_url)

                if self.news_data_list:
                    self.save_news_data_bulk(self.news_data_list)
                    self.news_data_list = []

                # 최종 세션 로그 저장
                self.finalize_session_log()
                success_message = f"SCRAPING COMPLETED FOR {self.scraper_name} WITH {self.session_log['total_records_processed']} RECORDS"
                self.process_info_log_msg(success_message, "scrape_news")
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = "THERE WAS AN ERROR WHILE SCRAPING NEWS\nCHECK THE LOGS FOR MORE DETAILS"
            self.process_err_log_msg(err_message, "scrape_news", stack_trace, e)

    def get_feed_entries(self):
        pass

    async def scrape_each_feed_entry(self, entry):
        pass


async def scrape_missing_news(df: pd.DataFrame, file_name: str):
    """Missing 뉴스 스크래퍼를 실행하는 함수"""
    scraper = MissingNewsScraper(scraper_name='missing_news_scraper', df=df, file_name=file_name)
    await scraper.scrape_news()


if __name__ == "__main__":
    asyncio.run(scrape_missing_news('missing_news.csv'))
