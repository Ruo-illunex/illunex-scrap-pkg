import traceback

import requests

from config import settings

api_url = settings.API_URL


# 데이터 조회
def get_scrap_managers(portal):
    response = requests.get(f"{api_url}?portal={portal}")
    if response.status_code == 200:
        return response.json()
    else:
        return None


# 데이터 삽입
def create_scrap_manager(scrap_manager_data):
    response = requests.post(api_url, json=scrap_manager_data)
    return response.status_code == 201


# 데이터 업데이트
def update_scrap_manager(id, scrap_manager_data):
    print("update_scrap_manager", id, scrap_manager_data)

    response = requests.put(f"{api_url}{id}", json=scrap_manager_data)
    return response.status_code == 200


def get_scrap_manager_by_id(id):
    response = requests.get(f"{api_url}{id}")
    if response.status_code == 200:
        return response.json()
    else:
        return None


def delete_scrap_manager(id):
    response = requests.delete(f"{api_url}{id}")
    return response.status_code == 204


# 로그 조회
def get_scraper_logs():
    response = requests.get(f"{api_url}monitoring/")
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
