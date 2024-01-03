import traceback
from typing import Optional

from app.common.log.log_config import setup_logger
from app.config.settings import FILE_PATHS
from app.common.core.utils import get_current_datetime, make_dir, get_current_date
from app.models_init import NewCompanyInfoPydantic, CollectDartPydantic
from app.database_init import companies_db


class DartInfoPreprocessing:
    def __init__(self):
        file_path = FILE_PATHS["log"] + 'preprocessing'
        make_dir(file_path)
        file_path += f'/dart_info_preprocessing_{get_current_datetime()}.log'
        self._logger = setup_logger(
            "dart_info_preprocessing",
            file_path
        )
        self._get_ksic()
        
    def _get_ksic(self):
        self._ksic_df = companies_db.get_ksic()   # [code_value, code_desc]
        # code_value = A01100 -> code: A, industry_code: 01100 분리 -> industry_code: 011로 뒤에 0 제거 (주의 앞에 0은 제거하지 않음)
        self._ksic_df['code'] = self._ksic_df['code_value'].apply(lambda x: x[0])   # A
        self._ksic_df['industry_code'] = self._ksic_df['code_value'].apply(lambda x: x[1:]) # 01100
        self._ksic_df['industry_code'] = self._ksic_df['industry_code'].apply(lambda x: x.rstrip('0'))  # 011

    def _search_ksic(self, industry_code: str) -> list:
        """업종코드를 통해 업종명을 찾는 함수
        Args:
            industry_code (str): 업종코드
        Returns:
            list: [code, industry_code, code_desc, representation_desc]
        """
        result = self._ksic_df[self._ksic_df['industry_code'] == industry_code].values.tolist() # [[code_value, code_desc, code, industry_code], ...]
        representation_code = result[0][2] + '00000'
        representation_desc = self._ksic_df[self._ksic_df['code_value'] == representation_code]['code_desc'].values[0]
        if result:
            result = result[0] + [representation_desc]
            return result
        else:
            return None

    def preprocess(self, data: CollectDartPydantic) -> Optional[NewCompanyInfoPydantic]:
        """OpenDartReader를 이용해 수집한 기업 정보를 DB에 저장하기 위해 전처리하는 함수
        Args:
            data (CollectDartPydantic): OpenDartReader를 이용해 수집한 기업 정보
        Returns:
            NewCompanyInfoPydantic: DB에 저장하기 위해 전처리한 기업 정보
        """
        try:
            # 기업 정보를 DB에 저장하기 위해 전처리
            listing_market_dict = {
                'Y': ('1', '코스피'),
                'K': ('2', '코스닥'),
                'N': ('3', '코넥스'),
                'E': ('9', '대상아님')
                }
            ksic = self._search_ksic(data.induty_code)    # [code, industry_code, code_desc]
            create_date, update_date = get_current_date(), get_current_date()
            company_info = NewCompanyInfoPydantic(
                id=data.company_id,
                bizNum=data.bizr_no,
                corporationNum=data.jurir_no,
                companyName=data.corp_name,
                realCompanyName=data.stock_name,
                representationName=data.ceo_nm,
                establishmentDate=data.est_dt,
                acctMonth=data.acc_mt,
                businessConditionCode=ksic[2] if ksic else None,
                businessConditionDesc=ksic[-1] if ksic else None,
                businessCategoryCode=ksic[2]+ksic[3] if ksic else None,
                businessCategoryDesc=ksic[1] if ksic else None,
                homepage=data.hm_url,
                tel=data.phn_no,
                fax=data.fax_no,
                address=data.adres,
                listingMarketId=listing_market_dict.get(data.corp_cls)[0],
                listingMarketDesc=listing_market_dict.get(data.corp_cls)[1],
                createDate=create_date,
                updateDate=update_date,
            )
            return company_info
        except Exception as e:
            err_msg = traceback.format_exc()
            self._logger.error(err_msg)
            self._logger.error(f"Error: {e}")
            return None
