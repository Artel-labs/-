FROM python:3.12.14 AS wheels

WORKDIR /wheels
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip wheel --wheel-dir /wheels -r requirements.txt

FROM python:3.12.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=wheels /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links /wheels -r /wheels/requirements.txt && rm -rf /wheels

WORKDIR /app
COPY backend/ .
RUN DJANGO_SECRET_KEY=collectstatic python manage.py collectstatic --noinput

RUN useradd --system --no-create-home dpo
USER dpo

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--worker-class", "gthread", "--threads", "4", "--timeout", "60", "--access-logfile", "-", "--no-control-socket"]
