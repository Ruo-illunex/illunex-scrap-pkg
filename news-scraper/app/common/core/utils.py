import datetime
import email.utils

import yaml


# YAML 파일 불러오는 함수
def load_yaml(path):
    with open(path, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            return exc


def preprocess_datetime_standard(date_str):
    """표준 날짜 형식 처리"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def preprocess_datetime_standard_without_seconds(date_str):
    """표준 날짜 형식 처리"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def preprocess_datetime_korean_without_seconds(date_str):
    """한국 날짜 형식 처리"""
    try:
        return datetime.datetime.strptime(date_str, '%Y년%m월%d일 %H:%M').strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def preprocess_datetime_compact(date_str):
    """압축된 날짜 형식 처리"""
    try:
        return datetime.datetime.strptime(date_str, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    

def preprocess_datetime_period_without_seconds(date_str):
    """표준 날짜 형식 처리"""
    try:
        return datetime.datetime.strptime(date_str, "%Y.%m.%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def preprocess_date_period(date_str):
    """표준 날짜 형식 처리"""
    try:
        return datetime.datetime.strptime(date_str, "%Y.%m.%d").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def preprocess_datetime_iso(date_str):
    """ISO 8601 날짜 형식 처리"""
    # ISO 8601 날짜 형식은 +00:00, +0000, +00 으로 끝날 수 있음
    if '+' in date_str:
        date_str = date_str.split('+')[0]
    try:
        return datetime.datetime.fromisoformat(date_str).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def preprocess_datetime_rfc2822(date_str):
    """RFC 2822 날짜 형식 처리"""
    try:
        return email.utils.parsedate_to_datetime(date_str).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
