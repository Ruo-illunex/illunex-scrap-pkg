### **수집기 v0.1 API 명세서**

- 작성자: 이루오 (ruo@illunex.com)

#### **1. 기본 정보**

- **Base URL**: `/api`
- **Description**: 수집기 v0.1은 다양한 뉴스 소스로부터 뉴스 데이터를 수집하는 RESTful API를 제공합니다.

#### **2. 엔드포인트**

##### 2.1. 뉴스 스크래핑 관련 엔드포인트

- **GET `/scrape`**

  - **Description**: 서비스 상태 확인 엔드포인트.
  - **Response**: 서비스 상태 메시지.
- **GET `/scrape/{source}_news`** (여기서 `{source}`는 `daum`, `naver`, `zdnet`, `vs`, `thebell`, `startupn`, `startuptoday`, `platum`, `esg_news`, `greenpost_news`, `esg_finance_news`, `esg_finance_hub` 중 하나)

  - **Description**: 지정된 뉴스 소스에서 뉴스를 스크래핑하는 엔드포인트.
  - **Response**: 스크래핑 시작 메시지 또는 에러 메시지.
- POST `/scrape/missing_news`

  - **Description**: 누락된 뉴스 URL이 담긴 CSV 파일을 받아 해당 뉴스를 스크래핑합니다.
  - **Request**: `multipart/form-data` 형식의 CSV 파일.
  - **Response**: 스크래핑 시작 메시지 또는 에러 메시지.

**사용 예제:**

```python
import requests

csv_file = '{파일명}.csv'
files = {"csv_file": (csv_file, open(csv_file, "rb"))}

response = requests.post(
    'http://172.30.1.100:8501/scrape/missing_news',
    files=files,
)

response_json = response.json()
print(response_json)
```

이 예제는 `missing_news.csv` 파일을 포함하는 POST 요청을 서버에 보내는 방법을 보여줍니다. 요청이 성공하면 서버는 누락된 뉴스 스크래핑을 시작하고 상태 메시지를 반환합니다.

##### 2.2. 스크랩 매니저 관련 엔드포인트 (router.py)

- **POST `/api/scrap_manager/`**

  - **Description**: 새로운 스크랩 매니저 데이터를 생성합니다.
  - **Request**: `ScrapManagerPydantic` 데이터.
  - **Response**: 생성된 `ScrapManagerPydantic` 객체.
- **GET `/api/scrap_manager/`**

  - **Description**: 지정된 포털별 스크랩 매니저 정보를 조회합니다.
  - **Query Parameter**: `portal` (포털 이름).
  - **Response**: `ScrapManagerWithIDPydantic` 객체 리스트.
- **GET `/api/scrap_manager/{id}`**

  - **Description**: 특정 ID를 가진 스크랩 매니저 정보를 조회합니다.
  - **Path Parameter**: `id` (스크랩 매니저 ID).
  - **Response**: `ScrapManagerPydantic` 객체.
- **PUT `/api/scrap_manager/{id}`**

  - **Description**: 특정 ID를 가진 스크랩 매니저 정보를 업데이트합니다.
  - **Path Parameter**: `id` (스크랩 매니저 ID).
  - **Request**: `ScrapManagerPydantic` 데이터.
  - **Response**: 업데이트된 `ScrapManagerPydantic` 객체.
- **DELETE `/api/scrap_manager/{id}`**

  - **Description**: 특정 ID를 가진 스크랩 매니저를 삭제합니다.
  - **Path Parameter**: `id` (스크랩 매니저 ID).
  - **Response**: 삭제 상태 메시지.
- **GET `/api/scrap_manager/monitoring/`**

  - **Description**: 스크래핑 매니저의 모니터링 데이터를 조회합니다.
  - **Response**: `scrap_session_logs` 및 `scrap_error_logs` 데이터.

#### **3. 에러 처리**

- 모든 엔드포인트는 예외 발생 시 상황에 맞는 HTTP 상태 코드와 오류 메시지를 반환합니다.
- 일반적인 오류 상태 코드는 `400` (Bad Request), `404` (Not Found), `500` (Internal Server Error) 등을 포함합니다.

#### **4. 로깅 및 모니터링**

- 애플리케이션은 모든 요청 및 응답을 로그로 기록하여 추적 및 문제 해결을 용이하게 합니다.
- `schedule` 라이브러리를 사용한 정기적인 모니터링 및 알림 기능이 포함되어 있습니다.
