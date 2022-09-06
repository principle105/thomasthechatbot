FROM --platform=linux/amd64 python:3.9-slim

WORKDIR /bot

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

RUN apt update

COPY . .

RUN pip install -U poetry

RUN poetry config virtualenvs.create false
RUN poetry install -E bot --no-interaction --no-ansi --without dev

CMD ["poetry", "run", "ttcbot"]              