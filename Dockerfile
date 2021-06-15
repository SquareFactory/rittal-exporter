FROM python:3.8-alpine as builder
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --target=/app/dependencies -r requirements.txt


FROM python:3.8-alpine

ENV PORT 8123
ENV PROMETHEUS_URL http://10.10.2.107:9090
ENV UPDATE_PERIOD_S 60
ENV PYTHONPATH="${PYTHONPATH}:/app/dependencies"

WORKDIR /app
COPY --from=builder	/app .
COPY main.py .

RUN apk add --no-cache tini

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["python3", "main.py"]
