import asyncio
import traceback
from datetime import datetime

import aiohttp
import pandas as pd
from pydantic import ValidationError

from app.database_init import collections_db, companies_db
from app.common.log.log_config import setup_logger
from app.config.settings import FILE_PATHS, DART_API_KEY
from app.common.core.utils import get_current_datetime, make_dir, get_corp_codes
from app.models_init import CollectDartNoticePydantic


class DartNoticeScraper:
    def __init__(self) -> None:
        file_path = FILE_PATHS["log"] + 'scrapers'
        make_dir(file_path)
        file_path += f'/dart_notice_scraper_{get_current_datetime()}.log'
        self._logger = setup_logger(
            "dart_notice_scraper",
            file_path
        )
        self._compids_and_corpcodes = collections_db.get_companyids_and_corpcodes()    # [(company_id, corp_code), ...]

        self._url = 'https://opendart.fss.or.kr/api/list.json'
        self._params = {'crtfc_key': DART_API_KEY}
        self._max_concurrent_main_tasks = 5
        self._max_concurrent_sub_tasks = 5
        self._delay_time = 2
    
    async def __aenter__(self):
        """세션 컨텍스트 매니저"""
        if not hasattr(self, 'session') or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """세션 컨텍스트 매니저"""
        if self.session:
            await self.session.close()

    async def _delay(self):
        """OpenDartReader API 호출 시 딜레이"""
        await asyncio.sleep(self._delay_time)

    async def __fetch_page(self, session, url, params, semaphore):
        async with semaphore:
            await self._delay()
            async with session.get(url, params=params) as response:
                return await response.json()

    async def _list_async(self, corp_code=None, start=None, end=None, kind=None, kind_detail=None, final=False) -> list:
        start = pd.to_datetime(start) if start else pd.to_datetime('1900-01-01')
        end = pd.to_datetime(end) if end else datetime.today()
        self._params['corp_code'] = corp_code if corp_code else ''
        self._params['bgn_de'] = start.strftime('%Y%m%d')
        self._params['end_de'] = end.strftime('%Y%m%d')
        self._params['last_reprt_at'] = 'Y' if final else 'N'
        self._params['pblntf_ty'] = kind if kind else ''
        self._params['pblntf_detail_ty'] = kind_detail if kind_detail else ''
        self._params['page_no'] = 1
        self._params['page_count'] = 100

        semaphore = asyncio.Semaphore(self._max_concurrent_sub_tasks)
        async with aiohttp.ClientSession() as session:
            first_page = await self.__fetch_page(session, self._url, self._params, semaphore)
            if 'status' in first_page and first_page['status'] != '000':
                raise ValueError(first_page)

            results = first_page.get('list', [])
            total_pages = first_page.get('total_page', 1)

            tasks = []
            for page in range(2, total_pages + 1):
                self._params['page_no'] = page
                task = asyncio.create_task(self.__fetch_page(session, self._url, self._params, semaphore))
                tasks.append(task)

            pages = await asyncio.gather(*tasks)
            for page in pages:
                results.extend(page.get('list', []))

            return results

    async def _scrape_company_dart_notice(self, company_id, corp_code, semaphore):
        async with semaphore:
            await self._delay()
            notice_data = []
            results = await self._list_async(corp_code=corp_code)
            for result in results:
                result['company_id'] = company_id
            try:
                notice_data = [CollectDartNoticePydantic(**result).dict() for result in results]
            except ValidationError as e:
                err_msg = f"Error: {e}\n{traceback.format_exc()}"
                self._logger.error(err_msg)
                return

            if notice_data:
                info_msg = collections_db.bulk_insert_collectdartnotice(notice_data)
                self._logger.info(info_msg)
                print(info_msg)

    async def scrape_dart_notice(self) -> None:
        """OpenDartReader를 이용해 모든 기업의 공시 정보를 수집하는 함수"""
        info_msg = f"Start: Scrape dart notice info"
        self._logger.info(info_msg)
        print(info_msg)

        main_semaphore = asyncio.Semaphore(self._max_concurrent_main_tasks)

        try:
            tasks = []
            for company_id, corp_code in self._compids_and_corpcodes:
                task = asyncio.create_task(self._scrape_company_dart_notice(company_id, corp_code, main_semaphore))
                tasks.append(task)

            await asyncio.gather(*tasks)

        except Exception as e:
            err_msg = f"Error: {e}\n{traceback.format_exc()}"
            self._logger.error(err_msg)
