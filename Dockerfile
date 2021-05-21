FROM python:3.9

ENV TERM xterm-256color
ENV PYTHONDONTWRITEBYTECODE="true"
ENV PYTHONPATH="/app"

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# When developing in conjuction with the API, uncomment this to use local version (instead of published PyPi version)
# RUN chmod +x ./bin/install-majortom-gateway.sh && ./bin/install-majortom-gateway.sh

ENTRYPOINT ["python3", "run.py"]
