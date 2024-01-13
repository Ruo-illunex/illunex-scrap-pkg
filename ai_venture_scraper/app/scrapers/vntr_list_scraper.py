import traceback
import pickle
from typing import Optional
import requests

from app.config.settings import FILE_PATHS
from app.common.core.utils import make_dir, get_current_datetime
from app.common.log.log_config import setup_logger


class VntrListScraper:
    def __init__(self) -> None:
        self._data_path = FILE_PATHS['data']
        self._log_path = FILE_PATHS['log'] + 'vntr_list_scraper'
        make_dir(self._log_path)
        self._log_path += f'/vntr_list_scraper_{get_current_datetime()}.log'
        self._logger = setup_logger(
            'vntr_list_scraper',
            self._log_path
        )
        self._url = 'https://www.smes.go.kr/venturein/pbntc/searchVntrCmpAction'
        self._headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json; charset=UTF-8',
            'Cookie': 'SESSION=298d9984-f5c2-460b-abba-e5350cc64dc4; __VCAP_ID__=1fed6c46-316a-4bb9-755b-a414; JSESSIONID=1572068D6DF871F2CF14BD105749EF9F; JSESSIONID=M1A1OlJ0xFEqNsk4ve0yvLv6xPiTUz4U4cAvZaNBp5KHanCCnNeBBKJBBp5Fywm9.VElQQS9zbWVzXzI=; SESSION_TTL=20240110171032',
            'Host': 'www.smes.go.kr',
            'Origin': 'https://www.smes.go.kr',
            'Referer': 'https://www.smes.go.kr/venturein/pbntc/searchVntrCmp',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        # 페이로드 설정
        self._payload = {
            'cmpNm': '',
            'rprsvNm': '',
            'bizRNo': '',
            'pg': '',
            'pageSize': 1,
            'areaCd': None,
            'sigunguAreaCd': '',
            'indstyCd': ''
        }

    def _get_response(self, page_size: int) -> Optional[dict]:
        """벤처기업 인증번호 목록을 가져오는 함수

        Args:
            page (int): 페이지 번호

        Returns:
            dict: 벤처기업 인증번호 목록
        """
        self._logger.info(f'Start getting response with {page_size} companies')
        self._payload['pageSize'] = page_size
        try:
            response = requests.post(
                self._url, json=self._payload, headers=self._headers
                )
            if response.status_code != 200:
                print(f'error! status code: {response.status_code}')
            else:
                return response.json()
        except Exception:
            self._logger.error(traceback.format_exc())
            return None

    def _get_totalcnt(self) -> int:
        """벤처기업 인증번호 목록의 최대 페이지 개수를 반환하는 함수

        Returns:
            int: 벤처기업 인증번호 목록의 최대 페이지 개수
        """
        self._logger.info('Start getting max_pagesize')
        result = self._get_response(1)
        if result is None:
            return 0
        totalcnt = result.get('TOTAL_COUNT', 0)
        self._logger.info(f'totalcnt: {totalcnt}')
        return totalcnt

    def _get_vntr_sn_indstycd_dict(self) -> None:
        """벤처기업 인증번호 목록을 가져오는 함수"""
        try:
            page_size = self._get_totalcnt()
            if page_size == 0:
                self._logger.warning('page_size is 0')
                return
            info_data = self._get_response(page_size)['DATA_LIST']
            vniasn_indstycd_dict = {row['vnia_sn']: row['indsty_cd'] for row in info_data}
            # vniasn_indstycd_dict를 pickle 파일로 저장
            with open(self._data_path+'vniasn_indstycd_dict.pkl', 'wb') as f:
                pickle.dump(vniasn_indstycd_dict, f)
            self._logger.info(f'successfully saved vniasn_indstycd_dict / length: {len(vniasn_indstycd_dict)}')
        except Exception:
            self._logger.error(traceback.format_exc())

    def read_vntr_sn_indstycd_dict(self) -> Optional[dict]:
        """vniasn_indstycd_dict.pkl 파일을 읽어서 벤처기업 인증번호 목록을 반환하는 함수

        Returns:
            list: 벤처기업 인증번호 목록
        """
        try:
            with open(self._data_path+'vniasn_indstycd_dict.pkl', 'rb') as f:
                vniasn_indstycd_dict = pickle.load(f)
                self._logger.info(f'successfully read vniasn_indstycd_dict / length: {len(vniasn_indstycd_dict)}')
                return vniasn_indstycd_dict
        except FileNotFoundError:
            self._logger.info('vniasn_indstycd_dict does not exist')
            self._get_vntr_sn_indstycd_dict()
            return self.read_vntr_sn_indstycd_dict()
        except Exception:
            self._logger.error(traceback.format_exc())
            return None
