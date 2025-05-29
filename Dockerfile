FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ARG NODE_MAJOR_VERSION=23
RUN apt-get update && apt-get install -y curl sqlite3 \
    && curl -fsSL https://deb.nodesource.com/setup_$NODE_MAJOR_VERSION.x | bash \
    && apt-get update && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man \
    && apt-get clean 

RUN mkdir /app
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

RUN env
COPY inventory /app/inventory
COPY binventory /app/binventory
COPY theme /app/theme
COPY pyproject.toml /app/
RUN uv pip install -r pyproject.toml
COPY . /app/

RUN python manage.py tailwind install --no-package-lock --no-input
RUN python manage.py tailwind build --no-input
RUN python manage.py collectstatic --no-input
RUN ls -lah /app/staticfiles
EXPOSE 8000

CMD ["./entrypoint.sh"]