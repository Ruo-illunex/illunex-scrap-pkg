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
        return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def preprocess_datetime_compact(date_str):
    """압축된 날짜 형식 처리"""
    try:
        return datetime.datetime.strptime(date_str, "%Y%m%d%H%M%S")
    except ValueError:
        return None


def preprocess_datetime_iso(date_str):
    """ISO 8601 날짜 형식 처리"""
    try:
        return datetime.datetime.fromisoformat(date_str)
    except ValueError:
        return None


def preprocess_datetime_rfc2822(date_str):
    """RFC 2822 날짜 형식 처리"""
    try:
        return email.utils.parsedate_to_datetime(date_str)
    except ValueError:
        return None
