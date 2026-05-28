FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      build-essential \
      curl \
      default-libmysqlclient-dev \
      pkg-config \
      git \
    && rm -rf /var/lib/apt/lists/*

COPY conf/requirements.txt /app/conf/requirements.txt
RUN pip install --no-cache-dir -r /app/conf/requirements.txt

COPY . /app

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
