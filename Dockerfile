FROM python:3.12-slim-bookworm

WORKDIR /app

COPY wheels /app/wheels
COPY requirements.txt /app/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-index --find-links=wheels -r requirements.txt && \
    rm -rf /app/wheels

#это зависимости cv2. К сожалению туча библиотек использует обучную, не headless версию. Козлы
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

#библиотеки для pyzbar
RUN apt-get install libzbar0 -y

COPY app.py /app/

ENTRYPOINT ["python3"]
CMD ["app.py"]

EXPOSE 8003
