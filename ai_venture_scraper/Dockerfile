FROM python:3.10.12-slim-bullseye

# 기본 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=on \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# 작업 디렉토리 설정
WORKDIR /usr/src/app

# 패키지 업데이트 및 필요한 도구 설치
RUN apt update -y && apt upgrade -y && \
    # 크롬 브라우저 설치를 위한 필요 패키지
    apt install -y wget gnupg2 && \
    # 크롬 브라우저 저장소 추가
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt update -y && \
    # 크롬 브라우저 설치
    apt install -y google-chrome-stable

# Poetry 설치
RUN pip install poetry==1.7.1

# Poetry 가상 환경 생성 비활성화
RUN poetry config virtualenvs.create false

# `pyproject.toml`과 `poetry.lock` 파일을 컨테이너에 복사
COPY pyproject.toml poetry.lock ./

# Poetry를 사용하여 의존성 설치
RUN poetry install --only main

# 애플리케이션 코드 복사
COPY . .

# 헬스체크 명령 추가
HEALTHCHECK --interval=5m --timeout=30s \
    CMD curl -f http://localhost:8080/health || exit 1

# 포트 설정
EXPOSE 8080

# 크롬 드라이버 권한 설정
RUN chmod +x app/config/chromedriver

# 서버 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
