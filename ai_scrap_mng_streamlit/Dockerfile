FROM python:3.10.12-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=on \
    PIP_DISABLE_PIP_VERSION_CHECK=on

COPY requirements.txt pyproject.toml poetry.lock /usr/src/

WORKDIR /usr/src

RUN apt update -y && apt upgrade -y

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

EXPOSE 8080

CMD ["streamlit", "run", "run.py", "--server.port=8080", "--server.address=0.0.0.0"]
