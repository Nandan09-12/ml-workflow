FROM python:3.12-alpine3.21

LABEL maintainer="nandu"

ENV PYTHONUNBUFFERED=1

COPY ./apps/api/requirements.txt /tmp/requirements.txt
COPY ./apps/api/requirements-dev.txt /tmp/requirements-dev.txt
COPY ./apps/api /app

WORKDIR /app
EXPOSE 8000

ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --no-cache --virtual .build-deps \
        gcc \
        musl-dev \
        libffi-dev \
        postgresql-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; then /py/bin/pip install -r /tmp/requirements-dev.txt; fi && \
    apk del .build-deps && \
    rm -rf /tmp && \
    adduser \
        --disabled-password \
        --no-create-home \
        app-user

ENV PATH="/py/bin:$PATH"

USER app-user

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
