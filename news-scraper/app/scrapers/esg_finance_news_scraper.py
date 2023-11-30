import asyncio
import random
import hashlib
import traceback
import types

import aiohttp
import requests
from bs4 import BeautifulSoup

from app.common.core.base_news_scraper import NewsScraper
from app.models_init import EsgNews
from app.scrapers.urls import URLs
from app.scrapers.esg_finance_hub_scraper import get_all_links_and_save_to_csv
from app.common.core.utils import preprocess_datetime_iso, preprocess_datetime_compact, preprocess_datetime_rfc2822, preprocess_datetime_standard


class EsgfinanceNewsScraper(NewsScraper):
    """ESG FINANCE 뉴스 스크래퍼 클래스"""

    def __init__(self, scraper_name: str):
        super().__init__(scraper_name)
        self.interval_time_sleep = 7200
        esgfinance_urls = URLs(scraper_name)
        self.headers = esgfinance_urls.headers
        urls = esgfinance_urls.urls
        self.news_board_url = urls['news_board_url']

    
    def get_all_links_and_save_to_csv(self):
        """모든 링크를 가져와서 CSV 파일에 저장하는 함수"""
        get_all_links_and_save_to_csv()


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
        
        try:
            raise ValueError(f"Invalid date format: {unprocessed_date}")
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE PROCESSING DATE: {unprocessed_date}"
            self.process_err_log_msg(err_message, "preprocess_datetime", stack_trace, e)
            return None



