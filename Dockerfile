FROM python:3.7
LABEL maintainer="James Turk <dev@jamesturk.net>"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING 'utf-8'
ENV LANG 'C.UTF-8'

RUN BUILD_DEPS=" \
      python3-dev \
      libpq-dev \
      wget \
    " \
    && apt-get update && apt-get install -y --no-install-recommends $BUILD_DEPS

ADD . /code/
WORKDIR /code/

RUN wget https://deb.nodesource.com/setup_lts.x -O nodesource.sh \
    && bash nodesource.sh \
    && apt install -y nodejs \
    && npm ci \
    && npm run build

RUN pip install -U pip poetry && poetry install

EXPOSE 8000
STOPSIGNAL SIGINT
ENTRYPOINT ["poetry", "run", "python", "-m", "bobsled.web"]
