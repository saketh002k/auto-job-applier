FROM python:3.11-slim

# Install dependencies for Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \

    wget gnupg2 ca-certificates unzip curl xvfb fonts-liberation libnss3 libxss1 libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxrandr2 libgbm1 libpangocairo-1.0-0 libpangox-1.0-0 libpango-1.0-0 libxext6 libxrender1 libglib2.0-0 libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Chromium and Chromedriver (matching)
RUN apt-get update && apt-get install -y chromium chromium-driver --no-install-recommends && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN pip install --upgrade pip && pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

EXPOSE 5000
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000", "--workers", "2"]
