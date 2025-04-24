FROM python:3.12-slim-bookworm

WORKDIR /app

COPY wheels /app/wheels
COPY requirements.txt /app/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-index --find-links=wheels -r requirements.txt && \
    rm -rf /app/wheels

COPY app.py /app/

ENTRYPOINT ["python3"]
CMD ["app.py"]

EXPOSE 8003
