import os
import datetime


def make_dir(path):
    """디렉토리 생성 함수

    Args:
        path (str): 생성할 디렉토리 경로
    """
    if not os.path.exists(path):
        os.makedirs(path)
        msg = f'Directory created: {path}'
        print(msg)
        return msg
    else:
        msg = f'Directory already exists: {path}'
        print(msg)
        return msg


def get_current_datetime():
    """현재 시간을 반환하는 함수

    Returns:
        str: 현재 시간 문자열
    """
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')


def get_current_date():
    """현재 날짜를 반환하는 함수

    Returns:
        str: 현재 날짜 문자열
    """
    return datetime.datetime.now().strftime('%Y-%m-%d')


def transform_img2byte(image_path: str) -> bytes:
    """이미지를 byte로 변환하는 함수
    args:
        image_path: 이미지 경로
    returns:
        image_bytes: 이미지를 byte로 변환한 객체
    """
    with open(image_path, 'rb') as image:
        image_bytes = image.read()
        return image_bytes
