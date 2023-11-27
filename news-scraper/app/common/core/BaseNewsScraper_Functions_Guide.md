# NewsScraper Documentation
- 작성자: 이루오 (ruo@illunex.com)

## 목차
1. [서론](#서론)
2. [클래스 설명](#클래스-설명)
   - [NewsScraper 클래스](#newsscraper-클래스)
   - [생성자 및 속성](#생성자-및-속성)
3. [메서드 설명](#메서드-설명)
   - [process_info_log_msg](#process_info_log_msg)
   - [process_err_log_msg](#process_err_log_msg)
   - [safe_extract](#safe_extract)
   - [extract_element](#extract_element)
   - [extract_news_details](#extract_news_details)
   - [process_news_data_or_error_log](#process_news_data_or_error_log)
   - [finalize_session_log](#finalize_session_log)
   - [fetch_url_with_retry](#fetch_url_with_retry)
4. [추상 메서드](#추상-메서드)
   - [get_news_urls](#get_news_urls)
   - [scrape_each_news](#scrape_each_news)
   - [preprocess_datetime](#preprocess_datetime)
   - [scrape_news](#scrape_news)
   - [get_feed_entries](#get_feed_entries)
   - [scrape_each_feed_entry](#scrape_each_feed_entry)
5. [사용 예시](#사용-예시)
6. [웹 페이지 데이터 안전 추출을 위한 safe_extract 함수 가이드](#웹-페이지-데이터-안전-추출을-위한-safe_extract-함수-가이드)


## 1. 서론
`base_news_scraper.py`는 뉴스 스크래핑을 위한 기본 클래스 및 유틸리티 함수를 제공합니다. 이 파일은 다양한 뉴스 소스에 대해 스크래핑 로직을 효율적으로 구현하는 데 필요한 기반 구조를 제공하는 추상 클래스 `NewsScraper`를 포함하고 있습니다.

## 2. 클래스 설명

### NewsScraper 클래스
`NewsScraper` 클래스는 뉴스 스크래핑을 위한 추상 클래스입니다. 다양한 뉴스 사이트에 대한 스크래핑 클래스가 이 클래스를 상속받아 구현됩니다.

#### 생성자 및 속성
- `__init__(scraper_name: str)`: 스크래퍼의 이름을 초기화합니다.
- `scraper_name (str)`: 스크래퍼의 이름.
- `current_time (str)`: 스크래핑이 시작된 현재 시간.
- `logger (Logger)`: 로깅을 위한 객체.
- `news_db (NewsDatabase)`: 뉴스 데이터베이스 관리 객체.
- `scraper_manager_db (ScraperManagerDatabase)`: 스크래퍼 관리 데이터베이스 객체.
- `session_log (dict)`: 세션 로그 정보.
- `error_logs (list)`: 발생된 에러 로그들의 리스트.
- `is_error (bool)`: 에러 발생 여부.
- `error_log (dict)`: 개별 에러 로그 정보.
- `parsing_rules_dict (dict)`: 파싱 규칙 딕셔너리.
- `category_dict (dict)`: 카테고리 딕셔너리.

## 3. 메서드 설명

### process_info_log_msg
- `process_info_log_msg(message: str, type: str="info")`: 정보, 성공, 경고 메시지를 로깅합니다.
- **Args**:
  - `message (str)`: 로깅할 메시지.
  - `type (str, optional)`: 로그의 타입 (info, success, warning).

### process_err_log_msg
- `process_err_log_msg(err_message: str, function_name: str, stack_trace: str = None, exception: Exception = None)`: 에러 메시지를 로깅합니다.
- **Args**:
  - `err_message (str)`: 에러 메시지.
  - `function_name (str)`: 함수 이름.
  - `stack_trace (str, optional)`: 스택 트레이스.
  - `exception (Exception, optional)`: 발생한 예외.

### safe_extract
- `safe_extract(soup, selector=None, attribute_name=None, default=None, find=False, tag=None, find_attributes=None, find_all=False)`: BeautifulSoup 객체에서 데이터를 안전하게 추출합니다.
- **Args**: 
  - `soup (BeautifulSoup)`: BeautifulSoup 객체.
  - `selector (str)`: CSS 선택자.
  - `attribute_name (str)`: 추출할 요소의 속성 이름.
  - `default (str)`: 기본 반환값.
  - `find (bool)`: find() 함수 사용 여부.
  - `tag (str)`: 검색할 HTML 태그 이름.
  - `find_attributes (dict)`: find() 또는 find_all()에서 사용할 속성 딕셔너리.
  - `find_all (bool)`: find_all() 함수 사용 여부.
- **Returns**:
  - `str` 또는 `list`: 추출된 데이터.

### extract_element
- `extract_element(soup: BeautifulSoup, parsing_rule: dict) -> str`: 뉴스 요소를 추출합니다.
- **Args**:
  - `soup (BeautifulSoup)`: BeautifulSoup 객체.
  - `parsing_rule (dict)`: 파싱 규칙 딕셔너리.
- **Returns**:
  - `data (str)`: 추출된 뉴스 요소.

### extract_news_details
- `extract_news_details(soup: BeautifulSoup, additional_data: list = [], parsing_rules_dict: dict = None) -> dict`: 뉴스 상세 정보를 추출합니다.
- **Args**:
  - `soup (BeautifulSoup)`: BeautifulSoup 객체.
  - `additional_data (list)`: 추가 데이터 리스트.
  - `parsing_rules_dict (dict)`: 파싱 규칙 딕셔너리.
- **Returns**:
  - `data (dict)`: 추출된 뉴스 상세 정보.

### process_news_data_or_error_log
- `process_news_data_or_error_log(news_data: dict, news_url: str)`: 스크랩한 뉴스 데이터 또는 에러 로그를 처리합니다.
- **Args**:
  - `news_data (dict)`: 스크랩한 뉴스 데이터.
  - `news_url (str)`: 뉴스 기사 URL.

### finalize_session_log
- `finalize_session_log()`: 스크래핑 세션의 로그를 최종적으로 저장합니다.

### fetch_url_with_retry
- `async fetch_url_with_retry(session: aiohttp.ClientSession, url: str, retries: int = 3) -> str`: 지정된 URL을 비동기적으로 재시도하며 요청합니다.
- **Args**:
  - `session (aiohttp.ClientSession)`: aiohttp 클라이언트 세션.
  - `url (str)`: 요청할 URL.
  - `retries (int)`: 재시도 횟수.


## 4. 추상 메서드
`NewsScraper` 클래스에는 구현되어야 하는 여러 추상 메서드가 있습니다. 이들은 서브클래스에서 구체적인 스크래핑 로직에 맞게

 구현되어야 합니다. 예를 들어:

### get_news_urls
- `get_news_urls(category: str=None)`: 카테고리별 뉴스 URL을 가져오는 추상 메서드.

### scrape_each_news
- `scrape_each_news(news_url: str, category: str=None, parsing_rules_dict: dict=None)`: 각 뉴스 기사를 스크래핑하는 추상 메서드.

### preprocess_datetime
- `preprocess_datetime(unprocessed_date: str) -> Optional[str]`: 날짜 데이터를 전처리합니다.
- **Args**:
  - `unprocessed_date (str)`: 처리되지 않은 날짜 데이터.
- **Returns**:
  - `processed_date (str)`: 전처리된 날짜 데이터.

### scrape_news
- `async scrape_news() -> None`: 뉴스 스크래핑을 실행합니다. 서브클래스에서 구체적인 구현이 필요합니다.

### get_feed_entries
- `get_feed_entries() -> Generator[dict, None, None]`: 뉴스 피드 엔트리를 가져옵니다. 서브클래스에서 구체적인 구현이 필요합니다.

### scrape_each_feed_entry
- `async scrape_each_feed_entry(feed_entry: dict) -> Optional[dict]`: 개별 뉴스 피드 엔트리를 스크래핑합니다.
- **Args**:
  - `feed_entry (dict)`: 뉴스 피드 엔트리.
- **Returns**:
  - `scraped_data (dict)`: 스크래핑된 데이터.

## 5. 사용 예시
이 섹션에서는 `NewsScraper` 클래스를 상속받아 구현된 서브클래스의 예시를 제공합니다. 이 예시는 다음과 같은 방법으로 스크래퍼를 구현하고 사용하는 방법을 보여줍니다:

```python
class SpecificNewsScraper(NewsScraper):
    ...
```


## 6. **웹 페이지 데이터 안전 추출을 위한 safe_extract 함수 가이드**
```python
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
```
이 `safe_extract` 함수는 BeautifulSoup을 사용하여 웹 페이지의 HTML에서 데이터를 추출하는 데 사용됩니다. 이 함수는 다양한 옵션을 제공하여 유연하게 사용할 수 있습니다. 아래에는 이 함수를 사용하는 방법에 대한 자세한 문서를 제공합니다.

### 6.1. 함수 설명
`safe_extract` 함수는 BeautifulSoup 객체를 사용하여 웹 페이지의 HTML 요소에서 데이터를 안전하게 추출하기 위한 함수입니다. 이 함수는 예외 처리를 포함하여 오류 발생 시 안정적으로 작동하도록 설계되었습니다.

### 6.2. 매개변수
- `soup (BeautifulSoup)`: 데이터를 추출할 웹 페이지의 BeautifulSoup 객체입니다.
- `selector (str)`: CSS 선택자를 사용하여 특정 HTML 요소를 선택할 수 있습니다. 예를 들어, `.class-name` 또는 `#id-name`.
- `attribute_name (str)`: 추출할 요소의 속성 이름입니다. 예를 들어, `href`, `src` 등이 있습니다.
- `default (str)`: 찾고자 하는 요소나 속성이 없을 경우 반환할 기본값입니다.
- `find (bool)`: `True`인 경우, `soup.find()` 함수를 사용하여 요소를 찾습니다.
- `tag (str)`: 찾고자 하는 HTML 태그의 이름입니다. 예를 들어, `div`, `span`, `a` 등이 있습니다.
- `find_attributes (dict)`: `find()` 또는 `find_all()` 함수에서 사용할 속성 딕셔너리입니다. 예: `{'class': 'some-class'}`.
- `find_all (bool)`: `True`인 경우, `soup.find_all()` 함수를 사용하여 모든 일치하는 요소를 찾습니다.

### 6.3. 반환 값
함수는 추출한 데이터를 문자열로 반환합니다. `find_all=True`인 경우에는 추출된 모든 요소를 리스트로 반환합니다.

### 6.4. 사용 예제
1. **단일 요소 추출하기:**
   ```python
   result = safe_extract(soup, selector='.example-class')
   ```

2. **특정 속성값 추출하기:**
   ```python
   image_src = safe_extract(soup, selector='img.example', attribute_name='src')
   ```

3. **find 함수 사용하기:**
   ```python
   paragraph = safe_extract(soup, find=True, tag='p', find_attributes={'class': 'story'})
   ```

4. **여러 요소 찾기:**
   ```python
   links = safe_extract(soup, find=True, tag='a', find_all=True)
   ```

### 6.5. 주의 사항
- 함수는 예외가 발생할 경우 주어진 `default` 값을 반환합니다.
- `selector`, `tag` 및 `find_attributes` 매개변수는 서로 상호 배타적입니다. 적절한 매개변수 조합을 사용하여 원하는 결과를 얻을 수 있습니다.
- `find_all=True`를 사용할 때는 반환 값이 리스트 형태임을 기억하세요.

이 문서를 참고하여 `safe_extract` 함수를 원하는 방식으로 활용해 보시기 바랍니다.