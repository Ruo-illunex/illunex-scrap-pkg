import datetime
import email.utils
import re

import yaml
import hanja


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


def preprocess_datetime_compact_with_seperator(date_str):
    """압축된 날짜 형식 처리"""
    try:
        return datetime.datetime.strptime(date_str, "%Y%m%dT%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
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


def preprocess_datetime_rfc3339(date_str):
    """GMT 기반 날짜 문자열을 표준 날짜 형식으로 변환"""
    try:
        dt = datetime.datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def preprocess_datetime_eng_without_seconds(date_str):
    """영문 날짜 형식 처리"""
    """'Published' 형식의 날짜 문자열을 표준 날짜 형식으로 변환"""
    try:
        # 정규 표현식을 사용하여 날짜와 시간 정보 추출
        match = re.search(r'(\d+):(\d+) (a\.m\.|p\.m\.) ET (\w+)\. (\d+), (\d+)', date_str)
        if not match:
            return None

        hour, minute, am_pm, month, day, year = match.groups()

        # 12시간제 시간을 24시간제로 변환
        hour = int(hour)
        if am_pm == 'p.m.' and hour != 12:
            hour += 12
        elif am_pm == 'a.m.' and hour == 12:
            hour = 0

        # 월을 숫자로 변환
        month = datetime.datetime.strptime(month, '%b').month

        # datetime 객체 생성
        dt = datetime.datetime(int(year), month, int(day), hour, int(minute))

        # 원하는 형식으로 출력
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        return None


def normal_text(in_str: str) -> str:
    rep_exp = r"[^a-zA-Z0-9가-힣]"
    temp1 = hanja.translate(in_str, "substitution")
    return re.sub(rep_exp, "", temp1)


def remove_emojis_and_special_chars(text):
    # 이모지 제거
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+", flags=re.UNICODE
        )
    text = emoji_pattern.sub(r'', text)

    # 특수 문자 제거 (옵션)
    text = re.sub(r'[^가-힣0-9a-zA-Z\s]', '', text)

    return text
