import time
import asyncio
import traceback

import OpenDartReader
import pandas as pd

from app.common.db.collections_database import CollectionsDatabase
from app.common.db.companies_database import CompaniesDatabase

from app.common.log.log_config import setup_logger
from app.config.settings import FILE_PATHS, DART_API_KEY
from app.common.core.utils import get_current_datetime, make_dir

from app.models_init import CollectDart, NewCompanyInfo, NewScrapCompanyDartInfo, CodeClass


class DartInfoScraper:
    def __init__(self) -> None:
        file_path = f'{FILE_PATHS["log"]}scrapers/dart_info_{get_current_datetime()}.log'
        make_dir(file_path)
        self.logger = setup_logger(
            "dart_info_scraper",
            file_path
        )
        self.opdr = OpenDartReader(DART_API_KEY)

        self.collections_db = CollectionsDatabase()
        self.company_id_dict = CompaniesDatabase().company_id_dict

    def _get_corp_code_list(self) -> pd.DataFrame:
        """OpenDartReader를 이용해 모든 기업의 고유번호 리스트를 가져오는 함수
        Returns:
            list: 고유번호 리스트
        """
        self.df_corp_codes = self.opdr.corp_codes