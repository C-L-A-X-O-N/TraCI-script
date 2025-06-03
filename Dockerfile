FROM ghcr.io/eclipse-sumo/sumo:latest

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/

RUN pip3 install --upgrade pip \
    && pip3 install -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

WORKDIR /app

COPY . .

ENV SUMO_HOME=/usr/share/sumo

CMD ["python3", "main.py"]