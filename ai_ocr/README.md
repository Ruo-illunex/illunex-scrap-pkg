# TROCR API 명세서 및 사용 예시

## 개요

TROCR API는 이미지 내의 텍스트를 추출하는 역할을 합니다. 이 API는 특히 캡챠 이미지와 같은 복잡한 이미지에서 텍스트를 식별하는 데 사용됩니다.

## API 사용 방법

### 1. TROCR 이미지 텍스트 추출 API

#### 엔드포인트

`POST /api/v1/trocr`

#### 요청

- `image`: 이미지 파일, PIL.Image 객체로 변환 가능 (예: `Image.open(image_path).convert("RGB")`)
- `max_length`: 추출할 텍스트의 최대 길이

#### 응답

- `status`: 상태 코드 (200 성공, 500 서버 에러)
- `text`: 추출된 텍스트

#### 예제

```python
@app.post("/api/v1/trocr")
async def get_text_from_trocr(image: UploadFile, max_length: int) -> dict:
    # TROCR 모델을 이용한 텍스트 추출
    ...
```

### 2. 이미지를 바이트로 변환하는 함수

#### 함수 설명

이미지 파일 경로를 받아 해당 이미지를 바이트로 변환합니다.

#### 사용 방법

- `image_path`: 이미지 파일의 경로

#### 반환 값

- `image_bytes`: 이미지의 바이트 형식

#### 예제

```python
def transform_img2byte(image_path: str) -> bytes:
    # 이미지 파일을 바이트로 변환
    ...
```

### 3. 캡챠 키 추출 함수

#### 함수 설명

캡챠 이미지 파일 경로와 스크래퍼 이름을 입력받아 캡챠 키를 추출합니다.

#### 사용 방법

- `file_path`: 캡챠 이미지 파일 경로
- `scraper_name`: 스크래퍼 이름

#### 반환 값

- `Optional[str]`: 추출된 캡챠 키 또는 실패 시 None

#### 예제

```python
def _get_captcha_key(self, file_path: str, scraper_name: str) -> Optional[str]:
    # 캡챠 키 추출
    ...
```

## 참고 사항

- 이미지 처리 중 발생하는 예외를 적절히 처리해야 합니다.
- 로깅을 통해 프로세스의 진행 상태를 추적할 수 있습니다.
- 서버 에러나 예외 발생 시 적절한 에러 메시지와 함께 상태 코드를 반환해야 합니다.
