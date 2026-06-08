FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

COPY crontab.txt /etc/cron.d/bible-study
RUN chmod 0644 /etc/cron.d/bible-study
RUN crontab /etc/cron.d/bible-study

RUN touch /var/log/bible-study.log

CMD ["sh", "-c", "service cron start && tail -f /var/log/bible-study.log"]