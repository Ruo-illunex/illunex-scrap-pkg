import asyncio
import traceback
from datetime import datetime

import aiohttp
import pandas as pd
from pydantic import ValidationError

from app.database_init import collections_db
from app.common.log.log_config import setup_logger
from app.config.settings import FILE_PATHS, DART_API_KEY
from app.common.core.utils import get_current_datetime, make_dir
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
        self._max_concurrent_main_tasks = 5
        self._max_concurrent_sub_tasks = 5
        self._delay_time = 2
        self._db_write_queue = asyncio.Queue()
    
    async def __aenter__(self):
        """세션 컨텍스트 매니저"""
        if not hasattr(self, 'session') or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """세션 컨텍스트 매니저"""
        if self.session:
            await self.session.close()

    async def _db_writer(self):
        """DB에 저장"""
        while True:
            data = await self._db_write_queue.get()
            info_msg = f"Start: Write to DB - Company ID: {data['company_id']} - Corp Code: {data['corp_code']}"
            self._logger.info(info_msg)
            print(info_msg)
            try:
                info_msg = collections_db.bulk_insert_collectdartnotice(data['notice_data'])
                self._db_write_queue.task_done()
                self._logger.info(info_msg)
                print(info_msg)
            except Exception as e:
                err_msg = f"Error: {e}\n{traceback.format_exc()}"
                self._logger.error(err_msg)

    async def _delay(self):
        """OpenDartReader API 호출 시 딜레이"""
        await asyncio.sleep(self._delay_time)

    async def __fetch_page(self, session, url, params, semaphore) -> dict:
        async with semaphore:
            await self._delay()
            page = params['page_no']
            try:
                async with session.get(url, params=params) as response:
                    info_msg = f"Corp_code: {params['corp_code']} - Page: {page}"
                    self._logger.info(info_msg)
                    print(info_msg)
                    return await response.json()
            except Exception as e:
                err_msg = f"Error: {e}\n{traceback.format_exc()}"
                self._logger.error(err_msg)
                return {}

    async def _list_async(self, corp_code=None, start=None, end=None) -> list:
        start = pd.to_datetime(start) if start else pd.to_datetime('1900-01-01')
        end = pd.to_datetime(end) if end else datetime.today()
        params = {
            'crtfc_key': DART_API_KEY,
            'corp_code': corp_code,
            'bgn_de': start.strftime('%Y%m%d'),
            'end_de': end.strftime('%Y%m%d'),
            'page_no': 1,
            'page_count': 100
        }

        semaphore = asyncio.Semaphore(self._max_concurrent_sub_tasks)
        async with aiohttp.ClientSession() as session:
            try:
                first_page = await self.__fetch_page(session, self._url, params, semaphore)
                if first_page != {}:
                    if first_page['status'] == '000':
                        results = first_page.get('list', [])
                        info_msg = f"Scraped: Corp_code: {params['corp_code']} - Page: 1"
                        total_pages = first_page.get('total_page', 1)

                        tasks = []
                        for page in range(2, total_pages + 1):
                            page_params = params.copy()
                            page_params['page_no'] = page
                            task = asyncio.create_task(self.__fetch_page(session, self._url, page_params, semaphore))
                            tasks.append(task)

                        pages = await asyncio.gather(*tasks)
                        for page in pages:
                            results.extend(page.get('list', []))
                            info_msg += f", {page['page_no']}"
                        self._logger.info(info_msg)
                        print(info_msg)
                        return results
                    else:
                        err_msg = f"Error: {first_page['status']}\n{first_page['message']}"
                        self._logger.error(err_msg)
                        print(err_msg)
                        return []
            except Exception as e:
                err_msg = f"Error: {e}\n{traceback.format_exc()}"
                self._logger.error(err_msg)
                return []

    async def _scrape_company_dart_notice(self, company_id, corp_code, semaphore):
        async with semaphore:
            await self._delay()

            info_msg = f"Start: Scrape dart notice info - Company ID: {company_id} - Corp Code: {corp_code}"
            self._logger.info(info_msg)
            print(info_msg)

            try:
                results = await self._list_async(corp_code=corp_code)
                notice_data = [CollectDartNoticePydantic(**result).dict() for result in results]
                for result in notice_data:
                    result['company_id'] = company_id

                if notice_data:
                    await self._db_write_queue.put(
                        {
                            'company_id': company_id,
                            'corp_code': corp_code,
                            'notice_data': notice_data
                        }
                    )
                return True  # 성공적으로 완료
            except Exception as e:  # ValidationError 또는 다른 예외를 포괄
                err_msg = f"Error: {e}\n{traceback.format_exc()}"
                self._logger.error(err_msg)
                return False  # 오류 발생

    async def scrape_dart_notice(self) -> None:
        """OpenDartReader를 이용해 모든 기업의 공시 정보를 수집하는 함수"""
        info_msg = f"Start: Scrape dart notice info"
        self._logger.info(info_msg)
        print(info_msg)

        main_semaphore = asyncio.Semaphore(self._max_concurrent_main_tasks)
        db_writer_task = asyncio.create_task(self._db_writer())
        try:
            tasks = []
            for company_id, corp_code in self._compids_and_corpcodes:
                task = asyncio.create_task(self._scrape_company_dart_notice(company_id, corp_code, main_semaphore))
                tasks.append(task)
            await asyncio.gather(*tasks)
            await self._db_write_queue.join()
        except Exception as e:
            err_msg = f"Error: {e}\n{traceback.format_exc()}"
            self._logger.error(err_msg)
        finally:
            db_writer_task.cancel()
            info_msg = f"End: Scrape dart notice info"
            self._logger.info(info_msg)
            print(info_msg)
