FROM python:3.12-slim-bookworm AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ARG NODE_MAJOR_VERSION=23
RUN apt-get update && apt-get install -y curl sqlite3 \
    && curl -fsSL https://deb.nodesource.com/setup_$NODE_MAJOR_VERSION.x | bash \
    && apt-get update && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man \
    && apt-get clean 

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

COPY pyproject.toml pyproject.toml
RUN uv pip install -r pyproject.toml

FROM python:3.12-slim-bookworm AS builder
COPY --from=base /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=base /usr/local/bin/ /usr/local/bin/
COPY --from=base /usr/bin/ /usr/bin/
COPY --from=base /usr/lib/node_modules/ /usr/lib/node_modules/
COPY --from=base /etc/alternatives/nodejs /etc/alternatives/nodejs

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

RUN mkdir /app
WORKDIR /app
COPY . /app/

RUN python manage.py tailwind install --no-package-lock --no-input
RUN python manage.py tailwind build --no-input
RUN python manage.py collectstatic --no-input

FROM python:3.12-slim-bookworm
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /app/ /app/
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

EXPOSE 8000

CMD ["./entrypoint.sh"]