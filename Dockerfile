FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

COPY requirements.txt .
# playwright install --with-deps already pulls every system lib chromium needs;
# apt/pip caches must be purged in this same layer or they stay in the image.
# main.py never sets channel=, so it runs on chromium-headless-shell already;
# --only-shell skips the redundant full-Chromium download.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps --only-shell chromium \
    && rm -rf /var/lib/apt/lists/*

COPY main.py .

EXPOSE 3000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
