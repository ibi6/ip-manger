FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATABASE_URL=sqlite:////data/ipam.db

WORKDIR /app

RUN groupadd --gid 10001 netledger \
    && useradd --uid 10001 --gid netledger --no-create-home --shell /usr/sbin/nologin netledger \
    && mkdir -p /data \
    && chown netledger:netledger /data

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY docker-entrypoint.sh /usr/local/bin/netledger-entrypoint

RUN chmod 0555 /usr/local/bin/netledger-entrypoint \
    && chown -R netledger:netledger /app

USER netledger

EXPOSE 8000

ENTRYPOINT ["netledger-entrypoint"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
