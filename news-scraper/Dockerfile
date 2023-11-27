FROM python:3.10.12-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1 \
    PIP_NO_CACHE_DIR=on \
    PIP_DISABLE_PIP_VERSION_CHECK=on

COPY requirements.txt pyproject.toml poetry.lock /usr/src/

WORKDIR /usr/src

RUN apt update -y && apt upgrade -y && \
    pip install -r requirements.txt && \
    poetry config virtualenvs.create false && \
    if [ -f pyproject.toml ]; then poetry install; fi

COPY . /usr/src/app
WORKDIR /usr/src/app/

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "5"]
