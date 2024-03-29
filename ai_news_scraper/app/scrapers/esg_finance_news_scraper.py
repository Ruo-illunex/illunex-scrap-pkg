import asyncio
import random
import hashlib
import traceback
import types
import glob
import os

import pandas as pd

from app.common.core.base_news_scraper import NewsScraper
from app.models_init import EsgNews
from app.scrapers.urls import URLs
from app.scrapers.esg_finance_hub_scraper import EsgFinanceHubScraper
from app.common.core.utils import *
from app.config.settings import FILE_PATHS
from app.common.core.utils import load_yaml, normal_text, truncate_content


class EsgfinanceNewsScraper(NewsScraper):
    """ESG FINANCE 뉴스 스크래퍼 클래스"""

    def __init__(self, scraper_name: str):
        super().__init__(scraper_name)
        self.interval_time_sleep = 7200
        esgfinance_urls = URLs(self.scraper_name)
        urls = esgfinance_urls.urls
        self.news_board_url = urls['news_board_url']
        self.esg_finance_hub_scraper = EsgFinanceHubScraper(scraper_name=self.scraper_name)
        self.media_name = None
        self.type1 = load_yaml(FILE_PATHS.get('esg_finance_media')).get('type1')
        self.type2 = load_yaml(FILE_PATHS.get('esg_finance_media')).get('type2')
        self.type3 = load_yaml(FILE_PATHS.get('esg_finance_media')).get('type3')
        self.type4 = load_yaml(FILE_PATHS.get('esg_finance_media')).get('type4')
        self.media = load_yaml(FILE_PATHS.get('esg_finance_media')).get('media')

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

    def get_news_urls(self):
        try:
            for link in self.esg_finance_hub_scraper.get_first_page_links():
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
                    domain = url.split('/')[2]
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
                    print(f'{self.media_name}: {url}\n')
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
        kind_id = self.category_dict.get(self.scraper_name).get("etc")
        norm_title = normal_text(title)
        content = truncate_content(content)

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
            # category="ESG",
            esg_analysis="",
            norm_title=norm_title,
            )
        return news_data

    async def scrape_news(self, get_all_news_urls=False):
        """뉴스를 스크래핑하는 함수"""
        is_loop = True
        while is_loop:
            try:
                # 세션 로그 초기화
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
                    if get_all_news_urls:
                        # 매 100개의 뉴스마다 데이터 베이스에 저장
                        if len(self.news_data_list) == 100:
                            self.save_news_data_bulk(self.news_data_list)
                            self.news_data_list = []

                # 뉴스 데이터베이스에 한 번에 저장
                self.save_news_data_bulk(self.news_data_list)

                # 최종 세션 로그 저장
                self.finalize_session_log()
                success_message = f"SCRAPING COMPLETED FOR {self.scraper_name} WITH {self.session_log['total_records_processed']} RECORDS"
                self.process_info_log_msg(success_message, "scrape_news")
            except Exception as e:
                stack_trace = traceback.format_exc()
                err_message = "THERE WAS AN ERROR WHILE SCRAPING NEWS"
                self.process_err_log_msg(err_message, "scrape_news", stack_trace, e)
                await asyncio.sleep(self.retry_delay)
            finally:
                if get_all_news_urls:
                    is_loop = False
                else:
                    # 모든 스크래핑이 끝나면 일정 시간 대기
                    await asyncio.sleep(self.interval_time_sleep)

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
