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
from app.models_init import CollectDartDocumentPydantic


class DartDocumentScraper:
    def __init__(self) -> None:
        pass
