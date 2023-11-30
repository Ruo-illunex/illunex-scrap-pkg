import traceback
from datetime import datetime
from io import StringIO

import requests
import pandas as pd

from config import settings

api_url = settings.API_URL


# 데이터 조회
def get_scrap_managers(portal):
    response = requests.get(f"{api_url}scrap_manager/?portal={portal}")
    if response.status_code == 200:
        return response.json()
    else:
        return None


# 데이터 삽입
def create_scrap_manager(scrap_manager_data):
    response = requests.post(f'{api_url}scrap_manager/', json=scrap_manager_data)
    return response.status_code == 201


# 데이터 업데이트
def update_scrap_manager(id, scrap_manager_data):
    print("update_scrap_manager", id, scrap_manager_data)

    response = requests.put(f"{api_url}scrap_manager/{id}", json=scrap_manager_data)
    return response.status_code == 200


def get_scrap_manager_by_id(id):
    response = requests.get(f"{api_url}scrap_manager/{id}")
    if response.status_code == 200:
        return response.json()
    else:
        return None


def delete_scrap_manager(id):
    response = requests.delete(f"{api_url}scrap_manager/{id}")
    return response.status_code == 204


# 로그 조회
def get_scraper_logs():
    response = requests.get(f"{api_url}scrap_manager/monitoring/")
    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_html(url):
    response = requests.get(url)
    return response.text


# soup에서 데이터 추출
def safe_extract(
        soup,
        selector=None,
        attribute_name=None,
        default=None,
        find=False,
        tag=None,
        find_attributes=None,
        find_all=False
        ):
    """
    soup에서 데이터를 안전하게 추출하는 함수.

    Args:
        soup (BeautifulSoup): BeautifulSoup 객체.
        selector (str): CSS 선택자.
        attribute_name (str): 추출할 요소의 속성 이름.
        default (str): 기본 반환값.
        find (bool): find() 함수 사용 여부.
        tag (str): 검색할 HTML 태그 이름.
        find_attributes (dict): find() 또는 find_all()에서 사용할 속성 딕셔너리.
        find_all (bool): find_all() 함수 사용 여부.

    Returns:
        str 또는 list: 추출된 데이터.
    """
    try:
        if selector:
            element = soup.select_one(selector) if not find_all else soup.select(selector)
        elif find and tag:
            element = soup.find(tag, find_attributes) if not find_all else soup.find_all(tag, find_attributes)
        else:
            return default

        if element:
            if find_all:
                return [el.get(attribute_name, default) if attribute_name else el.get_text().strip() for el in element]
            else:
                if attribute_name:
                    return element.get(attribute_name, default)
                else:
                    return element.get_text().strip()
        else:
            return default
    except Exception as e:
        # 예외 발생 시 스택 트레이스 출력
        stack_trace = traceback.format_exc()
        print(f"Error: {e}\n{stack_trace}")
        return default


# TimelineJS JSON 포맷에 맞춰서 데이터를 변환하는 함수 정의
def convert_to_timelinejs_format_with_colors(df):
    events = []
    color_map = {
        "daum": "#56A9FD",
        "naver": "#6FCF49",
        "thebell": "#D6C565",
        "startupn": "#E6A659",
        "startuptoday": "#0FA170",
        "venturesquare": "#FF8E75",
        "zdnet": "#956CC4",
        "platum": "#E671AF",
        "esgeconomy": "#7CADB6",
        "greenpostkorea": "#78D6B7",
    }
    default_color = "#575757"  # grey

    for _, row in df.iterrows():
        start_dt = datetime.fromisoformat(row['start_time'])
        end_dt = datetime.fromisoformat(row['end_time'])
        
        # remarks에 따라 색상을 매핑
        event_color = color_map.get(row['remarks'], default_color)
        
        event = {
            "media": {
                "url": "",
                "caption": "",
                "credit": ""
            },
            "start_date": {
                "year": start_dt.year,
                "month": start_dt.month,
                "day": start_dt.day,
                "hour": start_dt.hour,
                "minute": start_dt.minute,
                "second": start_dt.second,
                "millisecond": int(start_dt.microsecond / 1000),
                "format": ""
            },
            "end_date": {
                "year": end_dt.year,
                "month": end_dt.month,
                "day": end_dt.day,
                "hour": end_dt.hour,
                "minute": end_dt.minute,
                "second": end_dt.second,
                "millisecond": int(end_dt.microsecond / 1000),
                "format": ""
            },
            "text": {
                "headline": row['remarks'],
                "text": f"Total Records: {row['total_records_processed']}, "
                        f"Success: {row['success_count']}, "
                        f"Fail: {row['fail_count']}"
            },
            "group": "",
            "display_date": "",
            "background": {
                "url": "",
                "color": event_color
            },
            "media_credit": "",
            "media_caption": "",
            "media_thumbnail": "",
            "media_type": "",
            "link": "",
            "unique_id": row['log_id'],
            "autolink": ""
        }
        
        events.append(event)

    timelinejs_json_format_with_colors = {
        "title": {
            "media": {
                "url": "",
                "caption": "",
                "credit": ""
            },
            "text": {
                "headline": "Scrap Session Logs",
                "text": "A timeline of scrap session logs."
            }
        },
        "events": events
    }

    return timelinejs_json_format_with_colors


# fail_count가 있는 경우 경고색으로 배경색을 변경하는 기능 추가
def convert_to_timelinejs_format_with_alerts(df):
    events = []
    alert_color = "#FF5733"
    normal_color = "#28B463"

    for _, row in df.iterrows():
        start_dt = datetime.fromisoformat(row['start_time'])
        end_dt = datetime.fromisoformat(row['end_time'])

        # fail_count가 있는 경우 경고색 적용
        event_color = alert_color if row['fail_count'] > 0 else normal_color

        event = {
            "media": {
                "url": "",
                "caption": "",
                "credit": ""
            },
            "start_date": {
                "year": start_dt.year,
                "month": start_dt.month,
                "day": start_dt.day,
                "hour": start_dt.hour,
                "minute": start_dt.minute,
                "second": start_dt.second,
                "millisecond": int(start_dt.microsecond / 1000),
                "format": ""
            },
            "end_date": {
                "year": end_dt.year,
                "month": end_dt.month,
                "day": end_dt.day,
                "hour": end_dt.hour,
                "minute": end_dt.minute,
                "second": end_dt.second,
                "millisecond": int(end_dt.microsecond / 1000),
                "format": ""
            },
            "text": {
                "headline": row['remarks'],
                "text": f"Total Records: {row['total_records_processed']}, "
                        f"Success: {row['success_count']}, "
                        f"Fail: {row['fail_count']}"
            },
            "group": "",
            "display_date": "",
            "background": {
                "url": "",
                "color": event_color
            },
            "media_credit": "",
            "media_caption": "",
            "media_thumbnail": "",
            "media_type": "",
            "link": "",
            "unique_id": row['log_id'],
            "autolink": ""
        }
        
        events.append(event)

    timelinejs_json_format_with_alerts = {
        "title": {
            "media": {
                "url": "",
                "caption": "",
                "credit": ""
            },
            "text": {
                "headline": "Scrap Session Logs",
                "text": "A timeline of scrap session logs."
            }
        },
        "events": events
    }

    return timelinejs_json_format_with_alerts


# 스크랩 오류 로그의 URL 도메인에 따른 색상 매핑을 위한 color_map 생성
# 주어진 데이터에 기반하여 URL 도메인을 추출하고 색상을 할당합니다.
def create_color_map(df):
    # 도메인을 색상에 매핑하기 위한 기본 color_map 사전 정의
    color_map = {
        "v": "#56A9FD",
        "n": "#6FCF49",
        "thebell": "#D6C565",
        "startupn": "#E6A659",
        "startuptoday": "#4FCEA4",
        "venturesquare": "#FF8E75",
        "zdnet": "#956CC4",
        "platum": "#E671AF",
        "esgeconomy": "#7CADB6",
        "greenpostkorea": "#78D6B7",
    }

    # 모든 URL을 검사하여 도메인에 대한 색상이 color_map에 없으면 추가합니다.
    for url in df['url']:
        domain = url.split("//")[-1].split(".")[0]
        if domain not in color_map:
            # 새 도메인에 대한 색상을 랜덤하게 생성하거나 사전에 정의된 색상을 선택할 수 있습니다.
            # 여기서는 단순화를 위해 회색을 사용합니다.
            color_map[domain] = "#808080"  # 기본색상을 회색으로 설정합니다.

    return color_map


    # 스크랩 오류 로그 데이터를 TimelineJS JSON 형식으로 변환하는 함수
def convert_error_logs_to_timelinejs_format(df, color_map, default_color):
    events = []

    for _, row in df.iterrows():
        # 오류 시간 파싱
        error_time = datetime.fromisoformat(row['error_time'])
        
        # URL의 도메인에 따라 색상 매핑, 예를 들어 'startuptoday.co.kr'에서 'startuptoday' 추출
        domain_key = row['url'].split("//")[-1].split(".")[0]  # 도메인 키 추출
        event_color = color_map.get(domain_key, default_color)

        # 이벤트 객체 생성
        event = {
            "media": {
                "url": "",
                "caption": "",
                "credit": ""
            },
            "start_date": {
                "year": error_time.year,
                "month": error_time.month,
                "day": error_time.day,
                "hour": error_time.hour,
                "minute": error_time.minute,
                "second": error_time.second,
                "millisecond": int(error_time.microsecond / 1000),
                "format": ""
            },
            "text": {
                "headline": f"Error #{row['error_id']}",
                "text": f"Session ID: {row['session_log_id']}<br>"
                        f"URL: {row['url']}<br>"
                        f"Message: {row['error_message']}"
            },
            "background": {
                "url": "",
                "color": event_color
            },
            "unique_id": f"error_{row['error_id']}"
        }
        
        events.append(event)

    # 타임라인 JSON 포맷
    timeline_json = {
        "title": {
            "media": {
                "url": "",
                "caption": "",
                "credit": ""
            },
            "text": {
                "headline": "Scrap Error Logs",
                "text": "Timeline of errors encountered during scrap sessions."
            }
        },
        "events": events
    }

    return timeline_json


def get_data_from_api(portal):
    """API에서 데이터를 가져와 Pandas DataFrame으로 변환하는 함수
    args:
        portal (str): 포털 이름
    returns:
        df (DataFrame): API에서 가져온 데이터의 DataFrame
    """
    # API 엔드포인트 URL 구성
    url = f"{api_url}data/{portal}/"
    
    try:
        # API 호출
        response = requests.get(url)
        
        # 요청이 성공적이면
        if response.status_code == 200:
            # JSON 형식으로 데이터를 받음
            data_json = response.json()
            
            # Pandas DataFrame으로 변환
            df = pd.read_json(StringIO(data_json))
            return df
        else:
            # 요청에 실패하면 오류 메시지를 출력
            response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
