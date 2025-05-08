FROM python:3.12.10-slim-bookworm

WORKDIR /app

COPY distributed_yolo.py requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "distributed_yolo.py"]
CMD ["--help"]